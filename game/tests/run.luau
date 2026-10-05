-- Runs outside Roblox:  lune run tests/run.luau
local Grid = require("../src/shared/Grid")
local Inventory = require("../src/shared/Inventory")
local Codec = require("../src/shared/Codec")
local ProcessLogic = require("../src/shared/ProcessLogic")
local Recipes = require("../src/shared/Recipes")
local CraftLogic = require("../src/shared/CraftLogic")
local TradeLogic = require("../src/shared/TradeLogic")
local Wallet = require("../src/shared/Wallet")
local IslandGen = require("../src/shared/IslandGen")
local Defs = require("../src/shared/Defs")
local Stock = (require("../src/shared/Stock") :: any)(Defs)
local Config = require("../src/shared/Config")

local passed, failed = 0, 0
local function test(name: string, fn: () -> ())
	local ok, err = pcall(fn)
	if ok then
		passed += 1
	else
		failed += 1
		print("FAIL  " .. name .. "\n      " .. tostring(err))
	end
end
local function eq(a: any, b: any, what: string?)
	if a ~= b then
		error((what or "values") .. ": expected " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end

local function rulesFor(machine: string)
	return {
		recipes = Recipes.byMachine[machine],
		usesFuel = Recipes.usesFuel[machine] == true,
		fuel = Recipes.fuel,
		cap = 16,
		outCap = 8,
	}
end
local SMELTER = rulesFor("smelter")
local CHECKS = { isBlock = Defs.isBlock, isMachine = Defs.isMachine, maxCoord = Config.MAX_COORD }

-- Grid
test("key round trip, including negatives", function()
	local x, y, z = Grid.parseKey(Grid.key(-12, 3, 400))
	eq(x, -12)
	eq(y, 3)
	eq(z, 400)
end)
test("negative zero names the same cell as zero", function()
	eq(Grid.key(-0, 1, 2), Grid.key(0, 1, 2))
	eq(Grid.key(3, -0, -0), "3,0,0")
end)
test("parseKey rejects junk", function()
	eq(Grid.parseKey("1,2"), nil)
	eq(Grid.parseKey("a,b,c"), nil)
	eq(Grid.parseKey("1,2,3,4"), nil)
	eq(Grid.parseKey("1.5,2,3"), nil)
end)
test("four turns return to the start", function()
	for d = 0, 3 do
		eq(Grid.rotate(Grid.rotate(Grid.rotate(Grid.rotate(d, 1), 1), 1), 1), d)
	end
end)
test("direction vectors are unit steps and opposite pairs cancel", function()
	for d = 0, 3 do
		local dx, dz = Grid.dirVec(d)
		eq(math.abs(dx) + math.abs(dz), 1)
		local ox, oz = Grid.dirVec(Grid.rotate(d, 2))
		eq(dx + ox, 0)
		eq(dz + oz, 0)
	end
end)
test("world position maps to the cell that contains it", function()
	eq(Grid.toCell(0, 0, 3), 0)
	eq(Grid.toCell(1.4, 0, 3), 0)
	eq(Grid.toCell(1.6, 0, 3), 1)
	eq(Grid.toCell(-1.6, 0, 3), -1)
	eq(Grid.toCell(4096 + 6.2, 4096, 3), 2)
	for c = -5, 5 do
		eq(Grid.toCell(Grid.toWorld(c, 100, 3), 100, 3), c)
	end
end)
test("isInt rejects fractions, NaN, huge values and non-numbers", function()
	eq(Grid.isInt(3), true)
	eq(Grid.isInt(-3), true)
	eq(Grid.isInt(1.5), false)
	eq(Grid.isInt(0 / 0), false)
	eq(Grid.isInt(math.huge), false)
	eq(Grid.isInt("3"), false)
	eq(Grid.isInt(nil), false)
end)
test("isDir accepts only 0 to 3", function()
	eq(Grid.isDir(0), true)
	eq(Grid.isDir(3), true)
	eq(Grid.isDir(4), false)
	eq(Grid.isDir(-1), false)
	eq(Grid.isDir(1.5), false)
	eq(Grid.isDir("1"), false)
end)

-- Inventory
test("add then remove leaves nothing behind", function()
	local bag = {}
	eq(Inventory.add(bag, "coal", 5), true)
	eq(Inventory.count(bag, "coal"), 5)
	eq(Inventory.remove(bag, "coal", 5), true)
	eq(bag.coal, nil)
end)
test("cannot remove more than held", function()
	local bag = { coal = 2 }
	eq(Inventory.remove(bag, "coal", 3), false)
	eq(bag.coal, 2)
	eq(Inventory.remove(bag, "ore_fe", 1), false)
end)
test("rejects zero, negative, fractional and NaN amounts", function()
	local bag = { coal = 2 }
	for _, n in { 0, -1, 0.5, 0 / 0, math.huge } do
		eq(Inventory.add(bag, "coal", n), false)
		eq(Inventory.remove(bag, "coal", n), false)
	end
	eq(bag.coal, 2)
end)
test("sanitize drops unknown ids and bad counts", function()
	local bag =
		Inventory.sanitize({ coal = 3, nope = 5, iron_ore = -1, iron_ingot = 2.5, [7] = 1 }, Defs.isItem)
	eq(bag.coal, 3)
	eq(bag.nope, nil)
	eq(bag.iron_ore, nil)
	eq(bag.iron_ingot, nil)
	eq(next(Inventory.sanitize("junk", Defs.isItem)), nil)
end)

-- Processing machines
local function run(state, rules, seconds: number)
	for _ = 1, math.ceil(seconds / 0.2) do
		ProcessLogic.step(state, 0.2, rules)
	end
end
test("a smelter with ore but no fuel makes nothing", function()
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "ore_fe", 3, SMELTER)
	run(s, SMELTER, 60)
	eq(s.out.ingot_fe, nil)
	eq(s.buf.ore_fe, 3)
end)
test("one coal smelts exactly four ores", function()
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "coal", 1, SMELTER)
	ProcessLogic.insert(s, "ore_fe", 8, SMELTER)
	run(s, SMELTER, 120)
	eq(s.out.ingot_fe, 4)
	eq(s.buf.ore_fe, 4)
	eq(s.fuel, 0)
end)
test("an ingot takes the recipe's full time", function()
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "coal", 1, SMELTER)
	ProcessLogic.insert(s, "ore_fe", 1, SMELTER)
	ProcessLogic.step(s, 2.9, SMELTER)
	eq(s.out.ingot_fe, nil)
	ProcessLogic.step(s, 0.2, SMELTER)
	eq(s.out.ingot_fe, 1)
end)
test("work pauses when the output is full and resumes when it is taken", function()
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "coal", 8, SMELTER)
	ProcessLogic.insert(s, "ore_fe", 16, SMELTER)
	run(s, SMELTER, 600)
	eq(s.out.ingot_fe, SMELTER.outCap)
	eq(ProcessLogic.isWorking(s, SMELTER), false)
	eq(ProcessLogic.takeOutput(s), "ingot_fe")
	run(s, SMELTER, 4)
	eq(s.out.ingot_fe, SMELTER.outCap)
end)
test("no progress is banked while the machine cannot work", function()
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "ore_fe", 1, SMELTER)
	run(s, SMELTER, 50)
	ProcessLogic.insert(s, "coal", 1, SMELTER)
	ProcessLogic.step(s, 0.2, SMELTER)
	eq(s.out.ingot_fe, nil)
end)
test("machines refuse what they have no use for, and what does not fit", function()
	local s = ProcessLogic.new()
	eq(ProcessLogic.insert(s, "ore_fe", 99, SMELTER), 16)
	eq(ProcessLogic.insert(s, "ore_fe", 1, SMELTER), 0)
	eq(ProcessLogic.insert(s, "bread", 1, SMELTER), 0)
	eq(ProcessLogic.insert(s, "banana", 1, SMELTER), 0)
	-- a press burns nothing, so it does not take coal
	eq(ProcessLogic.insert(ProcessLogic.new(), "coal", 1, rulesFor("press")), 0)
end)
test("a press needs no fuel", function()
	local rules = rulesFor("press")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "ingot_fe", 2, rules)
	run(s, rules, 10)
	eq(s.out.plate_fe, 2)
end)
test("a kiln burns one log for each log it turns into charcoal", function()
	local rules = rulesFor("kiln")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "log", 4, rules)
	run(s, rules, 60)
	eq(s.out.charcoal, 2)
	eq(s.buf.log, nil)
end)
test("a kiln with a single log does not burn the log it is meant to cook", function()
	local rules = rulesFor("kiln")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "log", 1, rules)
	run(s, rules, 60)
	eq(s.buf.log, 1)
	eq(s.out.charcoal, nil)
end)
test("a blast furnace waits for both ingredients", function()
	local rules = rulesFor("blast")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "ingot_fe", 4, rules)
	run(s, rules, 60)
	eq(s.out.ingot_steel, nil)
	ProcessLogic.insert(s, "coal", 3, rules)
	run(s, rules, 60)
	eq(s.out.ingot_steel, 4)
end)
test("by-products come out with the main product", function()
	local rules = rulesFor("sawmill")
	local s = ProcessLogic.new()
	ProcessLogic.insert(s, "log", 1, rules)
	run(s, rules, 10)
	eq(s.out.plank, 4)
	eq(s.out.sawdust, 1)
end)
test("peeking shows the item that is then removed", function()
	local rules = rulesFor("sawmill")
	local s = ProcessLogic.new()
	eq(ProcessLogic.peekOutput(s), nil)
	ProcessLogic.insert(s, "log", 1, rules)
	run(s, rules, 10)
	local id = ProcessLogic.peekOutput(s) :: string
	local before = s.out[id]
	eq(ProcessLogic.removeOutput(s, id), true)
	eq((s.out[id] or 0), before - 1)
	eq(ProcessLogic.removeOutput(s, "banana"), false)
end)
test("stored machine state is cleaned on load", function()
	local s = ProcessLogic.sanitize({
		buf = { ore_fe = 999, banana = 3, coal = -2 },
		out = { ingot_fe = 2.9 },
		fuel = 0 / 0,
		progress = 77,
	}, SMELTER, Defs.isItem)
	eq(s.buf.ore_fe, 16)
	eq(s.buf.banana, nil)
	eq(s.buf.coal, nil)
	eq(s.out.ingot_fe, 2)
	eq(s.fuel, 0)
	eq(s.progress, 0)
	eq(next(ProcessLogic.sanitize("junk", SMELTER, Defs.isItem).buf), nil)
end)
test("every recipe only names items that exist, and every recipe machine exists", function()
	for machine, list in Recipes.byMachine do
		assert(Defs.isMachine(machine), "recipes for unknown machine " .. machine)
		for _, recipe in list do
			for id in recipe.ins do
				assert(Defs.isItem(id), machine .. " takes unknown item " .. id)
			end
			for id in recipe.outs do
				assert(Defs.isItem(id), machine .. " makes unknown item " .. id)
			end
			assert(recipe.secs > 0, machine .. " has a recipe that takes no time")
		end
	end
	for id in Recipes.fuel do
		assert(Defs.isItem(id), "unknown fuel " .. id)
	end
end)

-- Footprints
test("a one-cell machine covers only its own cell whichever way it faces", function()
	for d = 0, 3 do
		local cells = Grid.footprint(5, -2, d, 1, 1)
		eq(#cells, 1)
		eq(cells[1][1], 5)
		eq(cells[1][2], -2)
		local cx, cz = Grid.footprintCentre(d, 1, 1)
		eq(cx, 0)
		eq(cz, 0)
	end
end)
test("larger footprints have the right number of distinct cells and include the anchor", function()
	for _, size in { { 2, 1 }, { 2, 2 }, { 3, 3 } } do
		for d = 0, 3 do
			local cells = Grid.footprint(0, 0, d, size[1], size[2])
			eq(#cells, size[1] * size[2])
			local seen, anchor = {}, false
			for _, c in cells do
				local key = c[1] .. "," .. c[2]
				assert(not seen[key], "cell listed twice: " .. key)
				seen[key] = true
				anchor = anchor or (c[1] == 0 and c[2] == 0)
			end
			assert(anchor, "anchor cell missing")
		end
	end
end)
test("the footprint centre is the average of its cells", function()
	for _, size in { { 2, 1 }, { 2, 2 }, { 3, 3 } } do
		for d = 0, 3 do
			local sumX, sumZ = 0, 0
			local cells = Grid.footprint(4, 7, d, size[1], size[2])
			for _, c in cells do
				sumX += c[1]
				sumZ += c[2]
			end
			local cx, cz = Grid.footprintCentre(d, size[1], size[2])
			eq(4 + cx, sumX / #cells)
			eq(7 + cz, sumZ / #cells)
		end
	end
end)
test("a two-cell machine extends the way it faces", function()
	local fx, fz = Grid.dirVec(1)
	local cells = Grid.footprint(0, 0, 1, 2, 1)
	eq(cells[2][1], fx)
	eq(cells[2][2], fz)
end)

-- Codec
local function sortedKeys(blocks)
	local keys = {}
	for _, b in blocks do
		table.insert(keys, Grid.key(b.x, b.y, b.z) .. "=" .. b.id)
	end
	table.sort(keys)
	return table.concat(keys, ";")
end
test("the starter island survives a save and load unchanged", function()
	local blocks = IslandGen.generate()
	local island = {
		blocks = blocks,
		machines = { { id = "smelter", x = 1, y = 1, z = -2, d = 3, s = { fuel = 4, buf = { ore_fe = 2 } } } },
		bag = { coal = 7 },
	}
	local back, skipped = Codec.decode(Codec.encode(island), CHECKS)
	assert(back, "decode returned nil")
	eq(skipped, 0)
	eq(#back.blocks, #blocks)
	eq(sortedKeys(back.blocks), sortedKeys(blocks))
	eq(#back.machines, 1)
	eq(back.machines[1].id, "smelter")
	eq(back.machines[1].d, 3)
	eq(back.machines[1].s.fuel, 4)
	eq(back.bag.coal, 7)
end)
test("rows of blocks are stored as runs", function()
	local blocks = {}
	for x = -50, 49 do
		table.insert(blocks, { x = x, y = 0, z = 0, id = "stone" })
	end
	local enc = Codec.encode({ blocks = blocks, machines = {}, bag = {} })
	eq(#enc.b.stone, 4)
	eq(enc.b.stone[1], -50)
	eq(enc.b.stone[4], 100)
end)
test("random islands round trip", function()
	local ids = { "grass", "dirt", "stone", "planks", "tread" }
	for seed = 1, 20 do
		math.randomseed(seed)
		local seen, blocks = {}, {}
		for _ = 1, 300 do
			local x, y, z = math.random(-9, 9), math.random(-3, 3), math.random(-9, 9)
			local key = Grid.key(x, y, z)
			if not seen[key] then
				seen[key] = true
				table.insert(blocks, { x = x, y = y, z = z, id = ids[math.random(1, #ids)] })
			end
		end
		local back = Codec.decode(Codec.encode({ blocks = blocks, machines = {}, bag = {} }), CHECKS)
		assert(back, "decode returned nil")
		eq(sortedKeys(back.blocks), sortedKeys(blocks), "seed " .. seed)
	end
end)
test("decode refuses data it cannot trust", function()
	eq(Codec.decode(nil, CHECKS), nil)
	eq(Codec.decode("text", CHECKS), nil)
	eq(Codec.decode({ v = 99, b = {} }, CHECKS), nil)
	eq(Codec.decode({ b = {} }, CHECKS), nil)
end)
test("decode keeps the good entries and counts the bad ones", function()
	local raw = {
		v = 1,
		b = {
			stone = { 0, 0, 0, 2, 5, 0, 0, 0, 1.5, 0, 0, 1, 99999, 0, 0, 1 },
			unicorn = { 0, 0, 0, 1 },
			dirt = { 1, 2, 3 },
			grass = { 0, 0, 0, 1 },
		},
		m = {
			{ i = "belt", x = 3, y = 1, z = 0, d = 2 },
			{ i = "belt", x = 3, y = 1, z = 0, d = 0 },
			{ i = "belt", x = 4, y = 1, z = 0, d = 7 },
			{ i = "teleporter", x = 5, y = 1, z = 0, d = 0 },
			"junk",
		},
	}
	local back, skipped = Codec.decode(raw, CHECKS)
	assert(back, "decode returned nil")
	-- stone keeps 2 cells; the zero-length, fractional and out-of-range runs are dropped
	local stone = 0
	for _, b in back.blocks do
		if b.id == "stone" then
			stone += 1
		end
	end
	eq(stone, 2)
	eq(#back.machines, 1)
	eq(back.machines[1].d, 2)
	assert(skipped >= 8, "expected at least 8 skipped, got " .. skipped)
end)
test("a huge run cannot be used to flood the island", function()
	local back = Codec.decode({ v = 1, b = { stone = { 0, 0, 0, 2 ^ 30 } }, m = {} }, CHECKS)
	assert(back, "decode returned nil")
	eq(#back.blocks, 0)
end)

-- Island and definitions
test("the starter island has no two blocks in one cell and a floor under the spawn", function()
	local seen, floor = {}, false
	for _, b in IslandGen.generate() do
		local key = Grid.key(b.x, b.y, b.z)
		assert(not seen[key], "two blocks at " .. key)
		seen[key] = true
		assert(Defs.isBlock(b.id), "unknown block " .. b.id)
		if b.x == IslandGen.SPAWN.x and b.z == IslandGen.SPAWN.z and b.y == IslandGen.SPAWN.y - 1 then
			floor = true
		end
	end
	assert(floor, "nothing to stand on at the spawn")
	assert(
		not seen[Grid.key(IslandGen.SPAWN.x, IslandGen.SPAWN.y, IslandGen.SPAWN.z)],
		"spawn cell is filled"
	)
	assert(not seen[Grid.key(IslandGen.SPAWN.x, IslandGen.SPAWN.y + 1, IslandGen.SPAWN.z)], "no head room")
end)
test("every palette and hotbar entry is known, and every group is on a known tab", function()
	for _, group in Defs.Palette do
		assert(
			table.find(Defs.Tabs, group.tab),
			"group " .. group.name .. " is on unknown tab " .. tostring(group.tab)
		)
		assert(#group.ids > 0, "group " .. group.name .. " is empty")
		for _, entry in group.ids do
			assert(Defs.isEntry(entry), entry .. " is in the palette but is not a known thing")
			local machine = Defs.Machines[entry]
			assert(not (machine and machine.hidden), entry .. " is hidden but in the palette")
		end
	end
	for _, entry in Defs.DefaultHotbar do
		assert(Defs.isEntry(entry), entry .. " is on the hotbar but is not a known thing")
	end
	eq(#Defs.DefaultHotbar, 9)
end)
test("item entries are told apart from things to place", function()
	eq(Defs.itemOf("item:log"), "log")
	eq(Defs.itemOf("log"), nil)
	eq(Defs.itemOf("item:banana"), nil)
	eq(Defs.itemOf(42), nil)
	eq(Defs.name("item:ingot_fe"), Defs.Items.ingot_fe.name)
	eq(Defs.isPlaceable("item:log"), false)
end)
test("the on-island seller is not offered", function()
	eq(Defs.Machines.seller.hidden, true)
end)
test("machines only refer to things that exist", function()
	for id, def in Defs.Machines do
		if def.item then
			assert(Defs.isItem(def.item), id .. " makes unknown item " .. def.item)
		end
		for _, below in def.needsBelow or {} do
			assert(Defs.isBlock(below), id .. " needs unknown block " .. below)
		end
		for _, stage in def.stages or {} do
			assert(Defs.isMachine(stage), id .. " has unknown stage " .. stage)
		end
		if def.behavior == "processor" then
			assert(Recipes.byMachine[id], id .. " is a processor with no recipes")
		end
		assert(def.sx >= 1 and def.sz >= 1 and def.sy >= 1, id .. " has no size")
		assert(Defs.Machines[def.icon], id .. " has unknown icon " .. tostring(def.icon))
		if def.behavior == "extractor" then
			assert(#def.ports > 0, id .. " makes things but has no mouth")
		end
	end
end)
test("a block id is never also a machine id", function()
	for id in Defs.Blocks do
		assert(not Defs.isMachine(id), id .. " is used twice")
	end
end)

test("coins, tiers and mode travel with a stored island", function()
	local island = {
		blocks = {},
		machines = {},
		bag = {},
		profile = { mode = "survival", coins = 250, tiers = { basic = 2 } },
	}
	local back = Codec.decode(Codec.encode(island), CHECKS) :: any
	eq(back.profile.mode, "survival")
	eq(back.profile.coins, 250)
	eq(back.profile.tiers.basic, 2)
	-- an island stored before there was a profile still loads
	local old = Codec.decode(Codec.encode({ blocks = {}, machines = {}, bag = {} }), CHECKS) :: any
	eq(old.profile, nil)
end)

-- Bag keys
test("a bag key is an item, a machine, or a block with its prefix", function()
	eq(Stock.isKey("ingot_fe"), true)
	eq(Stock.isKey("smelter"), true)
	eq(Stock.isKey("block:planks"), true)
	eq(Stock.isKey("block:banana"), false)
	eq(Stock.isKey("planks"), false)
	eq(Stock.isKey("item:log"), false)
	eq(Stock.isKey(7), false)
	eq(Stock.blockOf("block:grass"), "grass")
	eq(Stock.blockOf("grass"), nil)
end)
test("broken blocks come back as the right thing", function()
	eq(Stock.blockDrop("stone", 0.5), "stone")
	eq(Stock.blockDrop("log", 0.5), "log")
	eq(Stock.blockDrop("dirt", 0.5), "dirt_clod")
	eq(Stock.blockDrop("grass", 0.5), "block:grass")
	eq(Stock.blockDrop("planks", 0.5), "block:planks")
	eq(Stock.blockDrop("leaves", 0.5), nil)
	eq(Stock.blockDrop("leaves", 0.01), "sapling")
end)
test("whatever a block breaks into can pay to place it again", function()
	for id in Defs.Blocks do
		local drop = Stock.blockDrop(id, 0.5)
		-- farmland is the exception: it has to be tilled, see the next test
		if drop and id ~= "farmland" then
			assert(Stock.isKey(drop), id .. " breaks into unknown " .. drop)
			assert(table.find(Stock.placeCost(id), drop), id .. " cannot be placed from " .. drop)
		end
	end
end)
test("dug-up farmland is dirt again and cannot be laid back down as farmland", function()
	eq(Stock.blockDrop("farmland", 0.5), "dirt_clod")
	eq(table.find(Stock.placeCost("farmland"), "dirt_clod"), nil)
	-- the dirt it leaves can still go down as dirt
	assert(table.find(Stock.placeCost("dirt"), "dirt_clod"), "a clod should place dirt")
end)
test("machines are placed from themselves, plants from their seed", function()
	eq(Stock.placeCost("smelter")[1], "smelter")
	eq(Stock.placeCost("plant_sapling")[1], "sapling")
	eq(Stock.placeCost("crop_wheat_1")[1], "seed")
	eq(Stock.machineReturn("smelter"), "smelter")
	eq(Stock.machineReturn("plant_sapling"), nil)
	eq(#Stock.placeCost("banana"), 0)
	for id, def in Defs.Machines do
		for _, key in Stock.placeCost(id) do
			assert(Stock.isKey(key), id .. " is paid for with unknown " .. key)
		end
		assert(not def.cost or Defs.isItem(def.cost), id .. " has an unknown cost")
	end
end)

-- Crafting
local function recipeFor(out: string)
	for _, recipe in Recipes.craft do
		if recipe.out == out then
			return recipe
		end
	end
	error("no recipe for " .. out)
end
test("every craft recipe, hand recipe and upgrade names only real things", function()
	for _, recipe in Recipes.craft do
		assert(Stock.isKey(recipe.out), "craft makes unknown " .. recipe.out)
		assert(recipe.n >= 1 and recipe.tier >= 0, recipe.out .. " has a bad count or tier")
		for key in recipe.ins do
			assert(Stock.isKey(key), recipe.out .. " uses unknown " .. key)
		end
	end
	for _, recipe in Recipes.hand do
		assert(not recipe.tool or Defs.isItem(recipe.tool), "unknown tool " .. tostring(recipe.tool))
		for key in recipe.ins do
			assert(Defs.isItem(key), "hand work uses unknown " .. key)
		end
		for key in recipe.outs do
			assert(Defs.isItem(key), "hand work makes unknown " .. key)
		end
	end
	for name, cost in Recipes.upgrades do
		assert(string.match(name, "^%a+:[23]$"), "odd upgrade name " .. name)
		for key in cost do
			assert(Stock.isKey(key), name .. " costs unknown " .. key)
		end
	end
end)
test("every bench a recipe asks for is a bench that can be placed", function()
	local kinds = { bag = true }
	for _, def in Defs.Machines do
		if def.behavior == "bench" then
			kinds[def.bench] = true
		end
	end
	for _, recipe in Recipes.craft do
		assert(kinds[recipe.bench], recipe.out .. " needs unknown bench " .. recipe.bench)
	end
	for _, recipe in Recipes.hand do
		assert(kinds[recipe.station], "hand work needs unknown station " .. recipe.station)
	end
end)
test("crafting in the bag needs no bench and uses up the ingredients", function()
	local bench = recipeFor("wb_basic")
	local bag = { plank = 20 }
	eq(CraftLogic.craft(bag, bench, {}, 2), true)
	eq(bag.wb_basic, 2)
	eq(bag.plank, 4)
end)
test("crafting fails whole when something is short, and says what", function()
	local frame = recipeFor("frame")
	local bag = { plate_fe = 2, rod_fe = 1 }
	local ok, reason, detail = CraftLogic.craft(bag, frame, { part = 1 }, 1)
	eq(ok, false)
	eq(reason, "missing")
	eq(detail, "rod_fe")
	eq(bag.plate_fe, 2)
	eq(bag.rod_fe, 1)
	eq(bag.frame, nil)
end)
test("crafting needs the right bench at a high enough tier", function()
	local frame = recipeFor("frame")
	local bag = { plate_fe = 2, rod_fe = 2 }
	local _, reason = CraftLogic.craft(bag, frame, {}, 1)
	eq(reason, "bench")
	_, reason = CraftLogic.craft(bag, frame, { basic = 3 }, 1)
	eq(reason, "bench")
	local smelter = recipeFor("smelter")
	local rich = {}
	for key, n in smelter.ins do
		rich[key] = n
	end
	_, reason = CraftLogic.craft(rich, smelter, { machine = smelter.tier - 1 }, 1)
	eq(reason, "tier")
	eq(CraftLogic.craft(rich, smelter, { machine = smelter.tier }, 1), true)
	eq(rich.smelter, 1)
	eq(next(rich, "smelter") == nil and next(rich) == "smelter", true)
end)
test("the unified workbench stands in for every workbench", function()
	local smelter = recipeFor("smelter")
	local bag = table.clone(smelter.ins)
	eq(CraftLogic.craft(bag, smelter, { all = 1 }, 1), true)
	-- but it is not a fire
	local smelt = nil
	for _, recipe in Recipes.hand do
		if recipe.station == "hand_furnace" and recipe.ins.ore_fe == 1 then
			smelt = recipe
		end
	end
	local ok, reason = CraftLogic.hand({ ore_fe = 1, coal = 1 }, smelt, { all = 1 }, 1, Recipes.fuel, 0)
	eq(ok, false)
	eq(reason, "bench")
end)
test("crafting refuses odd amounts", function()
	local bench = recipeFor("wb_basic")
	for _, times in { 0, -1, 1.5, 0 / 0, 1e9, "2" } do
		local bag = { plank = 1000000 }
		local ok, reason = CraftLogic.craft(bag, bench, {}, times :: any)
		eq(ok, false)
		eq(reason, "times")
		eq(bag.plank, 1000000)
	end
end)
local function handSmelt()
	for _, recipe in Recipes.hand do
		if recipe.station == "hand_furnace" and recipe.ins.ore_fe == 1 and recipe.outs.ingot_fe then
			return recipe
		end
	end
	error("no hand smelting recipe")
end
test("smelting by hand burns fuel and banks what is left of it", function()
	local bag = { ore_fe = 6, coal = 2 }
	local ok, _, _, banked = CraftLogic.hand(bag, handSmelt(), { hand_furnace = 1 }, 6, Recipes.fuel, 0)
	eq(ok, true)
	eq(bag.ingot_fe, 6)
	eq(bag.ore_fe, nil)
	eq(bag.coal, nil)
	eq(banked, 2)
	-- the banked heat pays for the next two
	bag.ore_fe = 2
	ok, _, _, banked = CraftLogic.hand(bag, handSmelt(), { hand_furnace = 1 }, 2, Recipes.fuel, banked)
	eq(ok, true)
	eq(bag.ingot_fe, 8)
	eq(banked, 0)
end)
test("hand smelting burns the weakest fuel first and fails whole without enough", function()
	local bag = { ore_fe = 3, log = 2, coal = 5 }
	eq(CraftLogic.hand(bag, handSmelt(), { hand_furnace = 1 }, 3, Recipes.fuel, 0), true)
	eq(bag.log, nil)
	eq(bag.coal, 4)
	local poor = { ore_fe = 3, log = 2 }
	local ok, reason, _, banked = CraftLogic.hand(poor, handSmelt(), { hand_furnace = 1 }, 3, Recipes.fuel, 0)
	eq(ok, false)
	eq(reason, "fuel")
	eq(poor.ore_fe, 3)
	eq(poor.log, 2)
	eq(banked, 0)
end)
test("hand work never burns what it is meant to work on", function()
	local char = nil
	for _, recipe in Recipes.hand do
		if recipe.ins.log and recipe.outs.charcoal then
			char = recipe
		end
	end
	if char and char.fuel then
		local bag = { log = char.ins.log }
		local ok, reason = CraftLogic.hand(bag, char, { [char.station] = 1 }, 1, Recipes.fuel, 0)
		eq(ok, false)
		eq(reason, "fuel")
		eq(bag.log, char.ins.log)
	end
end)
test("hand work that needs a tool keeps the tool", function()
	local press = nil
	for _, recipe in Recipes.hand do
		if recipe.tool == "hammer" and recipe.ins.ingot_fe == 1 and recipe.outs.plate_fe then
			press = recipe
		end
	end
	assert(press, "no hand recipe for iron plate")
	local bag = { ingot_fe = 2 }
	local ok, reason, detail = CraftLogic.hand(bag, press, { part = 1 }, 2, Recipes.fuel, 0)
	eq(ok, false)
	eq(reason, "tool")
	eq(detail, "hammer")
	bag.hammer = 1
	eq(CraftLogic.hand(bag, press, { part = 1 }, 2, Recipes.fuel, 0), true)
	eq(bag.hammer, 1)
	eq(bag.plate_fe, 2)
end)
test("a workbench is raised one tier at a time, with its cost, up to the top", function()
	local tiers = {}
	local bag = table.clone(Recipes.upgrades["basic:2"])
	local ok, reason = CraftLogic.upgrade(bag, tiers, {}, "basic", Recipes.upgrades)
	eq(reason, "bench")
	eq(CraftLogic.upgrade(bag, tiers, { basic = 1 }, "basic", Recipes.upgrades), true)
	eq(tiers.basic, 2)
	eq(next(bag), nil)
	ok, reason = CraftLogic.upgrade(bag, tiers, { basic = 2 }, "basic", Recipes.upgrades)
	eq(ok, false)
	eq(reason, "missing")
	eq(tiers.basic, 2)
	tiers.basic = 3
	ok, reason = CraftLogic.upgrade(bag, tiers, { basic = 3 }, "basic", Recipes.upgrades)
	eq(reason, "max")
	ok, reason = CraftLogic.upgrade(bag, tiers, { all = 1 }, "all", Recipes.upgrades)
	eq(reason, "kind")
end)
test("stored bench tiers are cleaned on load", function()
	local tiers =
		CraftLogic.sanitizeTiers({ basic = 2, tool = 9, part = 2.5, banana = 2, machine = "3", cook = 1 })
	eq(tiers.basic, 2)
	eq(tiers.tool, nil)
	eq(tiers.part, nil)
	eq(tiers.banana, nil)
	eq(tiers.machine, nil)
	eq(tiers.cook, nil)
	eq(next(CraftLogic.sanitizeTiers("junk")), nil)
end)

-- Coins
test("coins only move in whole positive amounts that exist", function()
	eq(Wallet.spend(100, 30), 70)
	eq(Wallet.spend(100, 100), 0)
	eq(Wallet.spend(100, 101), nil)
	eq(Wallet.add(100, 5), 105)
	for _, bad in { 0, -5, 1.5, 0 / 0, math.huge, "5" } do
		eq(Wallet.spend(100, bad :: any), nil)
		eq(Wallet.add(100, bad :: any), nil)
	end
	eq(Wallet.add(Wallet.MAX, 1), nil)
	eq(Wallet.sanitize(250, 7), 250)
	eq(Wallet.sanitize(-1, 7), 7)
	eq(Wallet.sanitize(2.5, 7), 7)
	eq(Wallet.sanitize("x", 7), 7)
end)

-- Trading
local function total(a, b, key: string): number
	return (a[key] or 0) + (b[key] or 0)
end
test("a trade swaps both offers and coins at once", function()
	local t = TradeLogic.new()
	local bagA, bagB = { ingot_fe = 10 }, { core_fe = 1, coal = 5 }
	eq(TradeLogic.setOffer(t, "a", "ingot_fe", 4, bagA), true)
	eq(TradeLogic.setCoins(t, "a", 500, 1000), true)
	eq(TradeLogic.setOffer(t, "b", "core_fe", 1, bagB), true)
	TradeLogic.setReady(t, "a", true)
	TradeLogic.setReady(t, "b", true)
	local ok, _, coinsA, coinsB = TradeLogic.complete(t, bagA, 1000, bagB, 200)
	eq(ok, true)
	eq(bagA.ingot_fe, 6)
	eq(bagA.core_fe, 1)
	eq(bagB.ingot_fe, 4)
	eq(bagB.core_fe, nil)
	eq(bagB.coal, 5)
	eq(coinsA, 500)
	eq(coinsB, 700)
end)
test("nobody can put up more than they hold", function()
	local t = TradeLogic.new()
	local ok, reason = TradeLogic.setOffer(t, "a", "ingot_fe", 5, { ingot_fe = 4 })
	eq(ok, false)
	eq(reason, "missing")
	ok, reason = TradeLogic.setCoins(t, "a", 11, 10)
	eq(reason, "missing")
	for _, bad in { -1, 1.5, 0 / 0, "3" } do
		eq(TradeLogic.setOffer(t, "a", "ingot_fe", bad :: any, { ingot_fe = 99 }), false)
		eq(TradeLogic.setCoins(t, "a", bad :: any, 99), false)
	end
	eq(TradeLogic.setOffer(t, "c", "ingot_fe", 1, { ingot_fe = 4 }), false)
	eq(next(t.a.offer), nil)
	eq(t.a.coins, 0)
end)
test("changing an offer un-readies both sides", function()
	local t = TradeLogic.new()
	local bagA = { ingot_fe = 10 }
	TradeLogic.setOffer(t, "a", "ingot_fe", 10, bagA)
	TradeLogic.setReady(t, "a", true)
	TradeLogic.setReady(t, "b", true)
	eq(TradeLogic.isAgreed(t), true)
	-- the classic trick: shrink the offer after the other side agreed
	TradeLogic.setOffer(t, "a", "ingot_fe", 1, bagA)
	eq(TradeLogic.isAgreed(t), false)
	eq(t.b.ready, false)
	local ok, reason = TradeLogic.complete(t, bagA, 0, {}, 0)
	eq(ok, false)
	eq(reason, "unready")
	eq(bagA.ingot_fe, 10)
end)
test("a trade fails whole if a side no longer holds what it put up", function()
	local t = TradeLogic.new()
	local bagA, bagB = { ingot_fe = 10 }, { coal = 5 }
	TradeLogic.setOffer(t, "a", "ingot_fe", 10, bagA)
	TradeLogic.setOffer(t, "b", "coal", 5, bagB)
	TradeLogic.setCoins(t, "b", 50, 50)
	TradeLogic.setReady(t, "a", true)
	TradeLogic.setReady(t, "b", true)
	bagA.ingot_fe = 3 -- spent elsewhere after agreeing
	local ok, reason, coinsA, coinsB = TradeLogic.complete(t, bagA, 0, bagB, 50)
	eq(ok, false)
	eq(reason, "changed")
	eq(bagA.ingot_fe, 3)
	eq(bagB.coal, 5)
	eq(coinsA, 0)
	eq(coinsB, 50)
	eq(TradeLogic.isAgreed(t), false)
	-- and likewise for coins
	bagA.ingot_fe = 10
	TradeLogic.setReady(t, "a", true)
	TradeLogic.setReady(t, "b", true)
	ok, reason = TradeLogic.complete(t, bagA, 0, bagB, 49)
	eq(reason, "changed")
end)
test("a trade never creates or destroys anything", function()
	math.randomseed(7)
	local keys = { "ingot_fe", "coal", "core_fe", "smelter", "block:planks" }
	for _ = 1, 300 do
		local bagA, bagB = {}, {}
		for _, key in keys do
			if math.random() < 0.7 then
				bagA[key] = math.random(1, 50)
			end
			if math.random() < 0.7 then
				bagB[key] = math.random(1, 50)
			end
		end
		local coinsA, coinsB = math.random(0, 1000), math.random(0, 1000)
		local before = {}
		for _, key in keys do
			before[key] = total(bagA, bagB, key)
		end
		local t = TradeLogic.new()
		for _, key in keys do
			TradeLogic.setOffer(t, "a", key, math.random(0, 60), bagA)
			TradeLogic.setOffer(t, "b", key, math.random(0, 60), bagB)
		end
		TradeLogic.setCoins(t, "a", math.random(0, 1200), coinsA)
		TradeLogic.setCoins(t, "b", math.random(0, 1200), coinsB)
		TradeLogic.setReady(t, "a", true)
		TradeLogic.setReady(t, "b", true)
		local _, _, afterA, afterB = TradeLogic.complete(t, bagA, coinsA, bagB, coinsB)
		eq(afterA + afterB, coinsA + coinsB)
		assert(afterA >= 0 and afterB >= 0, "a balance went negative")
		for _, key in keys do
			eq(total(bagA, bagB, key), before[key])
			assert(
				(bagA[key] or 1) > 0 and (bagB[key] or 1) > 0,
				"a zero or negative count was left in a bag"
			)
		end
	end
end)
test("a finished trade cannot be run again", function()
	local t = TradeLogic.new()
	local bagA, bagB = { ingot_fe = 2 }, {}
	TradeLogic.setOffer(t, "a", "ingot_fe", 1, bagA)
	TradeLogic.setReady(t, "a", true)
	TradeLogic.setReady(t, "b", true)
	eq(TradeLogic.complete(t, bagA, 0, bagB, 0), true)
	eq(TradeLogic.complete(t, bagA, 0, bagB, 0), false)
	eq(TradeLogic.setReady(t, "a", true), false)
	eq(TradeLogic.setOffer(t, "a", "ingot_fe", 1, bagA), false)
	eq(bagA.ingot_fe, 1)
	eq(bagB.ingot_fe, 1)
end)
test("one side can put up only so many different things", function()
	local t = TradeLogic.new()
	local bag = {}
	for i = 1, TradeLogic.MAX_KINDS + 1 do
		bag["k" .. i] = 1
	end
	for i = 1, TradeLogic.MAX_KINDS do
		eq(TradeLogic.setOffer(t, "a", "k" .. i, 1, bag), true)
	end
	local ok, reason = TradeLogic.setOffer(t, "a", "k" .. (TradeLogic.MAX_KINDS + 1), 1, bag)
	eq(ok, false)
	eq(reason, "kinds")
	-- changing one already on the table is still allowed
	eq(TradeLogic.setOffer(t, "a", "k1", 0, bag), true)
end)

print(string.format("%d passed, %d failed", passed, failed))
if failed > 0 then
	(require("@lune/process") :: any).exit(1)
end
