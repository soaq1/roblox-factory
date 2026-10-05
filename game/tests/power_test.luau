-- Electricity, assembly choices, and the processing rules they lean on:  lune run tests/power_test.luau
local T = require("./harness")
local PowerLogic = require("../src/shared/PowerLogic")
local AssemblyLogic = require("../src/shared/AssemblyLogic")
local ProcessLogic = require("../src/shared/ProcessLogic")
local Recipes = require("../src/shared/Recipes")
local Defs = require("../src/shared/Defs")

local test, eq = T.test, T.eq

local SET = { poleLink = 30, poleReach = 15, sourceReach = 8 }

local function near(a: number, b: number, what: string?)
	if math.abs(a - b) > 1e-6 then
		error((what or "values") .. ": expected about " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end
local function pole(key: string, x: number, z: number?)
	return { key = key, x = x, y = 0, z = z or 0, kind = "pole" }
end
local function source(key: string, x: number, supply: number, extra: any?)
	local d: any = { key = key, x = x, y = 0, z = 0, kind = "source", supply = supply }
	for k, v in extra or {} do
		d[k] = v
	end
	return d
end
local function load(key: string, x: number, demand: number, extra: any?)
	local d: any = { key = key, x = x, y = 0, z = 0, kind = "load", demand = demand }
	for k, v in extra or {} do
		d[k] = v
	end
	return d
end
local function battery(key: string, x: number, charge: number, extra: any?)
	local d: any =
		{ key = key, x = x, y = 0, z = 0, kind = "battery", charge = charge, capacity = 1000, rate = 50 }
	for k, v in extra or {} do
		d[k] = v
	end
	return d
end

-- Networks
test("a generator powers a machine standing next to it, with no pole", function()
	local r = PowerLogic.solve({ source("g", 0, 100), load("m", 6, 20) }, SET, 1)
	eq(r.powered.m, true)
	eq(r.net.m, r.net.g)
end)
test("a machine out of a lone generator's reach gets nothing", function()
	local r = PowerLogic.solve({ source("g", 0, 100), load("m", 9, 20) }, SET, 1)
	eq(r.powered.m, false)
	eq(r.net.m, nil)
	eq(r.throttle.g, 0)
end)
test("poles carry power down a line", function()
	local r = PowerLogic.solve({
		source("g", 0, 100),
		pole("p1", 10),
		pole("p2", 40),
		pole("p3", 70),
		load("m", 80, 20),
	}, SET, 1)
	eq(r.powered.m, true)
	eq(#r.links, 2)
	eq(r.links[1][1], "p1")
	eq(r.links[1][2], "p2")
end)
test("a gap in the line of poles cuts the machine off", function()
	local r =
		PowerLogic.solve({ source("g", 0, 100), pole("p1", 10), pole("p3", 70), load("m", 80, 20) }, SET, 1)
	eq(r.powered.m, false)
	eq(#r.links, 0)
end)
test("two separate networks do not share", function()
	local r = PowerLogic.solve({
		source("g1", 0, 100),
		load("m1", 5, 20),
		source("g2", 500, 10),
		load("m2", 505, 20),
	}, SET, 1)
	eq(r.powered.m1, true)
	eq(r.powered.m2, false)
	eq(r.net.m1.supply, 100)
	eq(r.net.m2.supply, 10)
end)
test("a pole alone gives nothing", function()
	local r = PowerLogic.solve({ pole("p", 0), load("m", 5, 20) }, SET, 1)
	eq(r.powered.m, false)
	eq(r.net.m.supply, 0)
end)

-- Shortage
test("when power is short, machines that cannot run without it come first", function()
	local r = PowerLogic.solve({
		source("g", 0, 50),
		load("a_boost", 3, 30),
		load("b_needs", 4, 30, { need = true }),
		load("c_needs", 5, 30, { need = true }),
	}, SET, 1)
	eq(r.powered.b_needs, true)
	eq(r.powered.c_needs, false)
	eq(r.powered.a_boost, false)
end)
test("a smaller machine further down the order still runs if it fits", function()
	local r = PowerLogic.solve({
		source("g", 0, 50),
		load("a", 3, 40, { need = true }),
		load("b", 4, 40, { need = true }),
		load("c", 5, 10, { need = true }),
	}, SET, 1)
	eq(r.powered.a, true)
	eq(r.powered.b, false)
	eq(r.powered.c, true)
end)
test("the same machines are chosen however the list is ordered", function()
	local devices =
		{ source("g", 0, 50), load("a", 3, 40, { need = true }), load("b", 4, 40, { need = true }) }
	local first = PowerLogic.solve(devices, SET, 1)
	local second = PowerLogic.solve({ devices[3], devices[2], devices[1] }, SET, 1)
	eq(first.powered.a, true)
	eq(second.powered.a, true)
	eq(second.powered.b, false)
end)
test("an idle machine counts as powered but draws nothing", function()
	local r = PowerLogic.solve({
		source("g", 0, 50),
		load("a", 3, 40, { need = true, idle = true }),
		load("b", 4, 40, { need = true }),
	}, SET, 1)
	eq(r.powered.a, true)
	eq(r.powered.b, true)
	eq(r.net.g.demand, 40)
	near(r.throttle.g, 0.8)
end)

-- Batteries
test("spare power charges a battery, up to its rate and its capacity", function()
	local r = PowerLogic.solve({ source("g", 0, 100), load("m", 3, 20), battery("b", 4, 0) }, SET, 2)
	near(r.charge.b, 100) -- 50 W for 2 s, though 80 W was spare
	near(r.throttle.g, 0.7) -- 20 W of load and 50 W of charging out of 100
	r = PowerLogic.solve({ source("g", 0, 100), battery("b", 4, 990) }, SET, 2)
	near(r.charge.b, 1000)
	near(r.throttle.g, 0.05)
end)
test("a battery covers a shortfall and runs down by exactly what it gave", function()
	local r = PowerLogic.solve(
		{ source("g", 0, 10), load("m", 3, 40, { need = true }), battery("b", 4, 500) },
		SET,
		2
	)
	eq(r.powered.m, true)
	near(r.charge.b, 500 - 30 * 2)
	eq(r.throttle.g, 1)
end)
test("an empty battery cannot hold a machine up", function()
	local r = PowerLogic.solve(
		{ source("g", 0, 10), load("m", 3, 40, { need = true }), battery("b", 4, 20) },
		SET,
		2
	)
	eq(r.powered.m, false) -- 20 J over 2 s is 10 W: 20 W in all, 40 wanted
	near(r.charge.b, 20 + 10 * 2) -- nothing ran, so the generator's 10 W went into the battery
end)
test("batteries on one network share the work in proportion", function()
	local r = PowerLogic.solve({
		source("g", 0, 0),
		load("m", 3, 60, { need = true }),
		battery("b1", 4, 1000),
		battery("b2", 5, 1000, { rate = 100 }),
	}, SET, 1)
	eq(r.powered.m, true)
	near(r.charge.b1, 1000 - 20)
	near(r.charge.b2, 1000 - 40)
end)
test("energy is neither made nor lost", function()
	math.randomseed(11)
	for _ = 1, 300 do
		local devices = { pole("p", 0) }
		local supply = math.random(0, 120)
		table.insert(devices, source("g", 5, supply))
		local held = 0
		for i = 1, math.random(0, 3) do
			local charge = math.random(0, 1000)
			held += charge
			table.insert(devices, battery("b" .. i, i, charge, { rate = math.random(10, 80) }))
		end
		for i = 1, math.random(0, 5) do
			table.insert(
				devices,
				load(
					"m" .. i,
					-i,
					math.random(5, 60),
					{ need = math.random() < 0.5, idle = math.random() < 0.2 }
				)
			)
		end
		local dt = math.random(1, 4) / 2
		local r = PowerLogic.solve(devices, SET, dt)
		local used, after = 0, 0
		for _, d in devices do
			if d.kind == "load" and r.powered[d.key] and not d.idle then
				used += d.demand
			elseif d.kind == "battery" then
				after += r.charge[d.key]
				assert(
					r.charge[d.key] >= -1e-6 and r.charge[d.key] <= d.capacity + 1e-6,
					"charge out of range"
				)
			end
		end
		-- what the generator actually gave, by its throttle, equals use plus the change in storage
		near(supply * r.throttle.g * dt, used * dt + (after - held), "energy balance")
		assert(r.throttle.g >= 0 and r.throttle.g <= 1, "throttle out of range")
	end
end)

-- Sources
test("fuel is only burned for what wind and sun do not cover", function()
	local r = PowerLogic.solve({
		pole("p", 0),
		source("wind", 3, 30, { free = true }),
		source("coal", 5, 100),
		load("m", 6, 50, { need = true }),
	}, SET, 1)
	eq(r.throttle.wind, 1)
	near(r.throttle.coal, 0.2)
	r = PowerLogic.solve(
		{ pole("p", 0), source("wind", 3, 30, { free = true }), source("coal", 5, 100), load("m", 6, 20) },
		SET,
		1
	)
	eq(r.throttle.coal, 0)
end)
test("a generator with nothing to power burns nothing", function()
	local r = PowerLogic.solve({ source("coal", 0, 100), pole("p", 5) }, SET, 1)
	eq(r.throttle.coal, 0)
end)
test("the endless reactor powers everything on the island, wherever it is", function()
	local r = PowerLogic.solve({
		source("reactor", 0, 1, { everywhere = true }),
		source("coal", 2000, 100),
		load("far", 5000, 9999, { need = true }),
		battery("b", -4000, 0),
	}, SET, 2)
	eq(r.powered.far, true)
	eq(r.net.far.endless, true)
	near(r.charge.b, 100)
	eq(r.throttle.coal, 0)
	eq(r.throttle.reactor, 1)
end)
test("wind and sun stay between nothing and full", function()
	local low, high = 1, 0
	for t = 0, 5000, 7 do
		local w = PowerLogic.wind(t, 3)
		assert(w >= 0 and w <= 1, "wind out of range")
		low, high = math.min(low, w), math.max(high, w)
		local s = PowerLogic.solar((t / 10) % 24, t)
		assert(s >= 0 and s <= 1, "sun out of range")
	end
	assert(low < 0.1 and high > 0.9, "wind should swing widely")
	eq(PowerLogic.solar(0, 100), 0)
	eq(PowerLogic.solar(3, 100), 0)
	assert(PowerLogic.solar(12, 0) > 0.7, "noon should be bright")
end)

-- Assembly
local function recipeFor(out: string)
	for index, recipe in Recipes.craft do
		if recipe.out == out then
			return index, recipe
		end
	end
	error("no recipe for " .. out)
end
test("every machine that is told what to make has something it can make", function()
	for _, id in { "assembler", "circuit", "manufacturer" } do
		local choices = AssemblyLogic.choices(id, Recipes.craft, Defs.isItem)
		assert(#choices > 0, id .. " has nothing to make")
		for _, index in choices do
			local recipe = Recipes.craft[index]
			assert(Defs.isItem(recipe.out), id .. " would make a non-item " .. recipe.out)
			for key in recipe.ins do
				assert(Defs.isItem(key), id .. " would need a non-item " .. key)
			end
		end
	end
end)
test("machines and blocks cannot be assembled, since they cannot ride a belt", function()
	local _, smelter = recipeFor("smelter")
	eq(AssemblyLogic.allowed("manufacturer", smelter, Defs.isItem), false)
	local _, planks = recipeFor("block:planks")
	eq(AssemblyLogic.allowed("manufacturer", planks, Defs.isItem), false)
	local _, extractor = recipeFor("extractor_fe")
	eq(AssemblyLogic.allowed("manufacturer", extractor, Defs.isItem), false)
end)
test("the assembler and circuit maker split the two-ingredient recipes between them", function()
	local seen = 0
	for _, recipe in Recipes.craft do
		local a = AssemblyLogic.allowed("assembler", recipe, Defs.isItem)
		local c = AssemblyLogic.allowed("circuit", recipe, Defs.isItem)
		assert(not (a and c), recipe.out .. " can be made by both")
		if a or c then
			seen += 1
			eq(AssemblyLogic.allowed("manufacturer", recipe, Defs.isItem), true)
		end
	end
	assert(seen > 0, "no two-ingredient recipes at all")
	local _, frame = recipeFor("frame")
	eq(AssemblyLogic.allowed("assembler", frame, Defs.isItem), true)
	eq(AssemblyLogic.allowed("circuit", frame, Defs.isItem), false)
end)
test("an assembly recipe runs through the processing rules", function()
	local _, frame = recipeFor("frame")
	local recipes = { AssemblyLogic.toProcess(frame) }
	local rules = { recipes = recipes, usesFuel = false, fuel = Recipes.fuel, cap = 16, outCap = 8 }
	local s = ProcessLogic.new()
	for key, n in frame.ins do
		eq(ProcessLogic.insert(s, key, n, rules), n)
	end
	eq(ProcessLogic.insert(s, "bread", 1, rules), 0)
	eq(ProcessLogic.hasWork(s, rules), true)
	ProcessLogic.step(s, AssemblyLogic.SECONDS - 0.1, rules)
	eq(s.out.frame, nil)
	ProcessLogic.step(s, 0.2, rules)
	eq(s.out.frame, frame.n)
	eq(ProcessLogic.hasWork(s, rules), false)
end)
test("a stored choice is found again by what it makes", function()
	local index, frame = recipeFor("frame")
	eq(AssemblyLogic.restore("assembler", Recipes.craft, Defs.isItem, index, "frame"), index)
	-- the position no longer matches: the name wins
	eq(AssemblyLogic.restore("assembler", Recipes.craft, Defs.isItem, index + 1, "frame"), index)
	eq(AssemblyLogic.restore("assembler", Recipes.craft, Defs.isItem, "junk", "frame"), index)
	eq(AssemblyLogic.restore("assembler", Recipes.craft, Defs.isItem, index, "banana"), nil)
	eq(AssemblyLogic.restore("assembler", Recipes.craft, Defs.isItem, index, 7), nil)
	eq(AssemblyLogic.restore("circuit", Recipes.craft, Defs.isItem, index, "frame"), nil)
	eq(frame.out, "frame")
end)

-- Processing rules added for this package
test("a buffer grows to fit a recipe that needs more than it normally holds", function()
	local recipes = Recipes.byMachine.coreforge
	assert(recipes, "the core forge has no recipes")
	local caps = ProcessLogic.caps(recipes, 16)
	local rules =
		{ recipes = recipes, usesFuel = false, fuel = Recipes.fuel, cap = 16, outCap = 8, caps = caps }
	for _, recipe in recipes do
		local s = ProcessLogic.new()
		for key, n in recipe.ins do
			eq(ProcessLogic.insert(s, key, n, rules), n, "room for " .. key)
		end
		eq(ProcessLogic.hasWork(s, rules), true)
		ProcessLogic.step(s, recipe.secs + 1, rules)
		for key, n in recipe.outs do
			eq(s.out[key], n)
		end
	end
end)
test("ordinary machines keep their ordinary buffers", function()
	eq(next(ProcessLogic.caps(Recipes.byMachine.smelter, 16)), nil)
	eq(next(ProcessLogic.caps(Recipes.byMachine.press, 16)), nil)
end)
test("stored contents of a large buffer survive loading", function()
	local recipes = Recipes.byMachine.coreforge
	local rules = {
		recipes = recipes,
		usesFuel = false,
		fuel = Recipes.fuel,
		cap = 16,
		outCap = 8,
		caps = ProcessLogic.caps(recipes, 16),
	}
	local s =
		ProcessLogic.sanitize({ buf = { stone = 1500, diamond = 99999, bread = 5000 } }, rules, Defs.isItem)
	eq(s.buf.stone, 1500)
	eq(s.buf.diamond, rules.caps.diamond)
	eq(s.buf.bread, 16)
end)
test("a machine on electricity gets twice the work from its fuel", function()
	local function ingots(perJob: number?)
		local rules = {
			recipes = Recipes.byMachine.smelter,
			usesFuel = true,
			fuel = Recipes.fuel,
			cap = 64,
			outCap = 64,
			fuelPerJob = perJob,
		}
		local s = ProcessLogic.new()
		ProcessLogic.insert(s, "coal", 1, rules)
		ProcessLogic.insert(s, "ore_fe", 20, rules)
		for _ = 1, 1000 do
			ProcessLogic.step(s, 0.2, rules)
		end
		return s.out.ingot_fe, s.fuel
	end
	local plain, plainLeft = ingots(nil)
	local saving, savingLeft = ingots(0.5)
	eq(plain, 4)
	eq(saving, 8)
	eq(plainLeft, 0)
	eq(savingLeft, 0)
end)
test("fuel never goes below nothing when the saving changes mid-way", function()
	local rules: any = {
		recipes = Recipes.byMachine.smelter,
		usesFuel = true,
		fuel = Recipes.fuel,
		cap = 64,
		outCap = 64,
		fuelPerJob = 0.5,
	}
	local s = ProcessLogic.new()
	s.fuel = 0.5
	ProcessLogic.insert(s, "ore_fe", 1, rules)
	rules.fuelPerJob = nil
	ProcessLogic.step(s, 10, rules)
	eq(s.out.ingot_fe, 1)
	eq(s.fuel, 0)
	eq(ProcessLogic.sanitize({ fuel = 2.5 }, rules, Defs.isItem).fuel, 2.5)
	eq(ProcessLogic.sanitize({ fuel = 2.7 }, rules, Defs.isItem).fuel, 2.5)
end)

-- Putting things into a machine by hand, and taking them out
local RateLogic = require("../src/shared/RateLogic")
local StoreLogic = require("../src/shared/StoreLogic")
local VendingLogic = require("../src/shared/VendingLogic")

local function rulesOf(machine: string)
	local recipes = Recipes.byMachine[machine]
	return {
		recipes = recipes,
		usesFuel = Recipes.usesFuel[machine] == true,
		fuel = Recipes.fuel,
		cap = 16,
		outCap = 8,
		caps = ProcessLogic.caps(recipes, 16),
	}
end
local function count(pile: { [string]: number }, key: string): number
	return pile[key] or 0
end

test("a hand puts in as many as fit, and exactly that many leave the bag", function()
	local rules = rulesOf("smelter")
	local s = ProcessLogic.new()
	local bag = { ore_fe = 40, coal = 3, bread = 5 }
	eq(ProcessLogic.deposit(s, bag, "ore_fe", 40, rules), 16)
	eq(bag.ore_fe, 24)
	eq(s.buf.ore_fe, 16)
	-- full: nothing more goes in and nothing leaves the bag
	eq(ProcessLogic.deposit(s, bag, "ore_fe", 5, rules), 0)
	eq(bag.ore_fe, 24)
	-- fuel is taken by a machine that burns it; all three, since that is all there is
	eq(ProcessLogic.deposit(s, bag, "coal", 99, rules), 3)
	eq(bag.coal, nil)
	-- something the machine has no use for stays in the bag
	eq(ProcessLogic.deposit(s, bag, "bread", 5, rules), 0)
	eq(bag.bread, 5)
end)
test("a hand cannot put in odd amounts or things it does not hold", function()
	local rules = rulesOf("smelter")
	local s = ProcessLogic.new()
	local bag = { ore_fe = 4 }
	for _, bad in { 0, -1, 1.5, 0 / 0, math.huge, "3" } do
		eq(ProcessLogic.deposit(s, bag, "ore_fe", bad :: any, rules), 0)
	end
	eq(ProcessLogic.deposit(s, bag, "coal", 2, rules), 0)
	eq(ProcessLogic.deposit(s, bag, 7 :: any, 2, rules), 0)
	eq(bag.ore_fe, 4)
	eq(next(s.buf), nil)
end)
test("taking from a slot brings all of that kind back to the bag", function()
	local rules = rulesOf("sawmill")
	local s = ProcessLogic.new()
	local bag = { log = 3 }
	ProcessLogic.deposit(s, bag, "log", 3, rules)
	for _ = 1, 20 do
		ProcessLogic.step(s, 0.2, rules)
	end
	local made = count(s.out, "plank")
	assert(made > 0, "the sawmill should have made planks")
	eq(ProcessLogic.withdraw(s, bag, "out", "plank"), made)
	eq(bag.plank, made)
	eq(s.out.plank, nil)
	local left = count(s.buf, "log")
	eq(ProcessLogic.withdraw(s, bag, "buf", "log"), left)
	eq(count(bag, "log"), left)
	-- nothing there, or no such slot: nothing moves
	eq(ProcessLogic.withdraw(s, bag, "out", "plank"), 0)
	eq(ProcessLogic.withdraw(s, bag, "fuel", "log"), 0)
	eq(ProcessLogic.withdraw(s, bag, "buf", 7 :: any), 0)
end)
test("hands and the machine together never make or lose anything", function()
	math.randomseed(11)
	local rules = rulesOf("press")
	for _ = 1, 100 do
		local s = ProcessLogic.new()
		local bag = { ingot_fe = math.random(1, 60) }
		local metal = bag.ingot_fe
		for _ = 1, 30 do
			local roll = math.random()
			if roll < 0.4 then
				ProcessLogic.deposit(s, bag, "ingot_fe", math.random(1, 20), rules)
			elseif roll < 0.6 then
				ProcessLogic.withdraw(s, bag, if math.random() < 0.5 then "buf" else "out", "ingot_fe")
			elseif roll < 0.8 then
				ProcessLogic.withdraw(s, bag, "out", "plate_fe")
			else
				ProcessLogic.step(s, math.random() * 3, rules)
			end
			-- one ingot becomes one plate, so ingots and plates together stay the same
			local total = count(bag, "ingot_fe")
				+ count(s.buf, "ingot_fe")
				+ count(bag, "plate_fe")
				+ count(s.out, "plate_fe")
			eq(total, metal)
		end
	end
end)
test("a machine says why it has stopped", function()
	local rules = rulesOf("smelter")
	local s = ProcessLogic.new()
	eq(ProcessLogic.status(s, rules, {}), "waiting")
	ProcessLogic.insert(s, "ore_fe", 4, rules)
	eq(ProcessLogic.status(s, rules, {}), "nofuel")
	ProcessLogic.insert(s, "coal", 1, rules)
	eq(ProcessLogic.status(s, rules, {}), "working")
	eq(ProcessLogic.status(s, rules, { halted = true }), "halted")
	eq(ProcessLogic.status(s, rules, { needsPower = true }), "nopower")
	eq(ProcessLogic.status(s, rules, { needsPower = true, powered = true }), "working")
	-- a signal outranks missing power, since it is the player's own doing
	eq(ProcessLogic.status(s, rules, { halted = true, needsPower = true }), "halted")
end)
test("a full output or a stuck exit reads as blocked", function()
	local rules = rulesOf("smelter")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "ore_fe", 16, rules)
	ProcessLogic.insert(s, "coal", 8, rules)
	for _ = 1, 400 do
		ProcessLogic.step(s, 0.2, rules)
	end
	eq(ProcessLogic.status(s, rules, {}), "blocked")
	-- one product waiting and unable to leave is also blocked, even though there is room for more
	local t = ProcessLogic.new()
	t.out.ingot_fe = 1
	eq(ProcessLogic.status(t, rules, { stuck = true }), "blocked")
	eq(ProcessLogic.status(t, rules, {}), "waiting")
	-- "stuck" with nothing waiting means nothing
	eq(ProcessLogic.status(ProcessLogic.new(), rules, { stuck = true }), "waiting")
end)
test("a kiln holding only the log it is meant to cook is out of fuel, not waiting", function()
	local rules = rulesOf("kiln")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "log", 1, rules)
	eq(ProcessLogic.status(s, rules, {}), "nofuel")
	ProcessLogic.insert(s, "log", 1, rules)
	eq(ProcessLogic.status(s, rules, {}), "working")
end)
test("what a machine takes is its ingredients, plus fuel if it burns any", function()
	local smelter = ProcessLogic.wanted(Recipes.byMachine.smelter, true, Recipes.fuel)
	eq(smelter.ore_fe, true)
	eq(smelter.coal, true)
	eq(smelter.bread, nil)
	local press = ProcessLogic.wanted(Recipes.byMachine.press, false, Recipes.fuel)
	eq(press.ingot_fe, true)
	eq(press.coal, nil)
	eq(next(ProcessLogic.wanted({}, false, Recipes.fuel)), nil)
end)

-- Measured output
test("the rate is what left in the last minute, and old output drops away", function()
	local meter = RateLogic.new()
	eq(RateLogic.perMinute(meter, 100), 0)
	RateLogic.add(meter, 100, 1)
	RateLogic.add(meter, 103, 2)
	RateLogic.add(meter, 130, 4)
	eq(RateLogic.perMinute(meter, 131), 7)
	-- the first three were more than a minute ago by now
	eq(RateLogic.perMinute(meter, 170), 4)
	eq(RateLogic.perMinute(meter, 300), 0)
	RateLogic.add(meter, 300, 0)
	RateLogic.add(meter, 300, -3)
	eq(RateLogic.perMinute(meter, 300), 0)
end)
test("a steady machine reads a steady rate", function()
	local meter = RateLogic.new()
	for second = 0, 600, 2 do
		RateLogic.add(meter, second, 1)
	end
	local rate = RateLogic.perMinute(meter, 600)
	assert(rate >= 28 and rate <= 31, "one every two seconds should read about 30 a minute, got " .. rate)
end)

-- Chests
test("a chest move carries exactly what it says, in full or not at all", function()
	local bag, chest = { log = 10, smelter = 2 }, {}
	eq(StoreLogic.move(bag, chest, "log", 4), 4)
	eq(bag.log, 6)
	eq(chest.log, 4)
	-- asking for more than there is moves all there is
	eq(StoreLogic.move(bag, chest, "log", 99), 6)
	eq(bag.log, nil)
	eq(chest.log, 10)
	-- machines and blocks are stored the same way
	eq(StoreLogic.move(bag, chest, "smelter", 1), 1)
	eq(StoreLogic.move(chest, bag, "log", 2 ^ 30), 10)
	eq(bag.log, 10)
	eq(chest.log, nil)
end)
test("a chest move refuses nonsense and moves nothing", function()
	local bag, chest = { log = 10 }, { log = 1 }
	for _, bad in { 0, -2, 0.5, 0 / 0, math.huge, "4", 2 ^ 31 } do
		eq(StoreLogic.move(bag, chest, "log", bad :: any), 0)
	end
	eq(StoreLogic.move(bag, chest, "banana", 1), 0)
	eq(StoreLogic.move(bag, chest, 5 :: any, 1), 0)
	eq(StoreLogic.move(bag, bag, "log", 1), 0)
	eq(bag.log, 10)
	eq(chest.log, 1)
	-- a pile that would overflow takes nothing
	local huge = { log = 2 ^ 31 - 2 }
	eq(StoreLogic.move(bag, huge, "log", 5), 0)
	eq(bag.log, 10)
end)
test("moving between a bag and a chest never makes or loses anything", function()
	math.randomseed(23)
	local keys = { "log", "ingot_fe", "smelter", "block:planks" }
	for _ = 1, 200 do
		local bag, chest = {}, {}
		local before = {}
		for _, key in keys do
			bag[key] = math.random(0, 40)
			chest[key] = math.random(0, 40)
			before[key] = bag[key] + chest[key]
			if bag[key] == 0 then
				bag[key] = nil
			end
			if chest[key] == 0 then
				chest[key] = nil
			end
		end
		for _ = 1, 20 do
			local key = keys[math.random(1, #keys)]
			local roll = math.random()
			if roll < 0.45 then
				StoreLogic.move(bag, chest, key, math.random(1, 50))
			elseif roll < 0.9 then
				StoreLogic.move(chest, bag, key, math.random(1, 50))
			else
				StoreLogic.moveAll(chest, bag)
			end
			for _, k in keys do
				eq(count(bag, k) + count(chest, k), before[k])
				assert((bag[k] or 1) > 0 and (chest[k] or 1) > 0, "a zero or negative count was left behind")
			end
		end
	end
end)
test("emptying a chest moves every kind and counts them", function()
	local bag, chest = { log = 1 }, { log = 4, coal = 6 }
	eq(StoreLogic.moveAll(chest, bag), 10)
	eq(next(chest), nil)
	eq(bag.log, 5)
	eq(bag.coal, 6)
	local kinds, total = StoreLogic.totals(bag)
	eq(kinds, 2)
	eq(total, 11)
end)

-- Power reach, as the preview draws it
test("the reach numbers the preview uses are the ones the power system uses", function()
	local s = PowerLogic.settings(3)
	eq(s.poleLink, PowerLogic.REACH_CELLS.poleLink * 3)
	eq(s.poleReach, PowerLogic.REACH_CELLS.poleReach * 3)
	eq(s.sourceReach, PowerLogic.REACH_CELLS.sourceReach * 3)
end)
test("the preview joins exactly what the power system joins", function()
	local s = PowerLogic.settings(3)
	local function spot(kind: string, x: number)
		return { x = x, y = 0, z = 0, kind = kind }
	end
	-- a pole: other poles within the link distance, generators within its reach
	local reach, joined = PowerLogic.preview(spot("pole", 0), {
		spot("pole", s.poleLink),
		spot("pole", s.poleLink + 1),
		spot("source", s.poleReach),
		spot("source", s.poleReach + 1),
		spot("battery", 1),
	}, s)
	eq(reach, s.poleReach)
	eq(#joined, 2)
	eq(joined[1], 1)
	eq(joined[2], 3)
	-- a generator: poles whose reach it stands in, generators close by
	reach, joined = PowerLogic.preview(spot("source", 0), {
		spot("pole", s.poleReach),
		spot("source", s.sourceReach),
		spot("source", s.sourceReach + 1),
	}, s)
	eq(reach, s.sourceReach)
	eq(#joined, 2)
	-- and the solver agrees: a pole and a generator this far apart share a network
	local result = PowerLogic.solve({
		{ key = "p", x = 0, y = 0, z = 0, kind = "pole" },
		{ key = "g", x = s.poleReach, y = 0, z = 0, kind = "source", supply = 100 },
		{ key = "m", x = -s.poleReach, y = 0, z = 0, kind = "load", demand = 20, need = true },
	}, s, 1)
	eq(result.powered.m, true)
end)
test("the endless reactor and a battery have no reach ball of their own", function()
	local s = PowerLogic.settings(3)
	eq((PowerLogic.preview({ x = 0, y = 0, z = 0, kind = "source", everywhere = true }, {}, s)), 0)
	eq((PowerLogic.preview({ x = 0, y = 0, z = 0, kind = "battery" }, {}, s)), 0)
end)

-- The vending machine's sign
test("a vending machine is off until it has an item and a price", function()
	local v = VendingLogic.new()
	eq(VendingLogic.shopState(v, 1000), "off")
	local bag = { ingot_fe = 10 }
	local function isKey(key)
		return key == "ingot_fe"
	end
	eq(VendingLogic.configure(v, bag, "ingot_fe", 0, "sell", 64, isKey), false)
	eq(VendingLogic.shopState(v, 1000), "off")
	eq(VendingLogic.configure(v, bag, "ingot_fe", 14, "sell", 64, isKey), true)
	eq(VendingLogic.shopState(v, 1000), "empty")
	VendingLogic.deposit(v, bag, 3)
	eq(VendingLogic.shopState(v, 1000), "open")
end)
test("a buying machine shows when its owner cannot pay or it has bought enough", function()
	local v = VendingLogic.new()
	local function isKey(key)
		return key == "ingot_fe"
	end
	VendingLogic.configure(v, {}, "ingot_fe", 14, "buy", 2, isKey)
	eq(VendingLogic.shopState(v, 13), "nomoney")
	eq(VendingLogic.shopState(v, 14), "open")
	v.stock = 2
	eq(VendingLogic.shopState(v, 1000), "full")
end)

T.done()
