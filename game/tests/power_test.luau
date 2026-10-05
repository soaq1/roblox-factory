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

T.done()
