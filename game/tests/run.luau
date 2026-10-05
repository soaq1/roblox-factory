-- Runs outside Roblox:  lune run tests/run.luau
local Grid = require("../src/shared/Grid")
local Inventory = require("../src/shared/Inventory")
local Codec = require("../src/shared/Codec")
local SmelterLogic = require("../src/shared/SmelterLogic")
local IslandGen = require("../src/shared/IslandGen")
local Defs = require("../src/shared/Defs")
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

local RULES = { smeltTime = 3, fuelPerCoal = 4, maxFuel = 16, maxOre = 8, maxOut = 4 }
local CHECKS = { isBlock = Defs.isBlock, isMachine = Defs.isMachine, maxCoord = Config.MAX_COORD }

-- Grid
test("key round trip, including negatives", function()
	local x, y, z = Grid.parseKey(Grid.key(-12, 3, 400))
	eq(x, -12)
	eq(y, 3)
	eq(z, 400)
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
	eq(Inventory.remove(bag, "iron_ore", 1), false)
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

-- Smelter
test("no fuel means no ingots", function()
	local s = SmelterLogic.new()
	SmelterLogic.insert(s, "iron_ore", 3, RULES)
	SmelterLogic.step(s, 100, RULES)
	eq(s.out, 0)
	eq(s.ore, 3)
end)
test("one coal smelts exactly four ores", function()
	local s = SmelterLogic.new()
	SmelterLogic.insert(s, "coal", 1, RULES)
	SmelterLogic.insert(s, "iron_ore", 8, RULES)
	for _ = 1, 100 do
		SmelterLogic.step(s, 0.2, RULES)
		SmelterLogic.takeOutput(s, 99)
	end
	eq(s.ore, 4)
	eq(s.fuel, 0)
end)
test("an ingot takes the full smelt time", function()
	local s = SmelterLogic.new()
	SmelterLogic.insert(s, "coal", 1, RULES)
	SmelterLogic.insert(s, "iron_ore", 1, RULES)
	SmelterLogic.step(s, 2.9, RULES)
	eq(s.out, 0)
	SmelterLogic.step(s, 0.2, RULES)
	eq(s.out, 1)
end)
test("stops when the output is full and resumes when it is taken", function()
	local s = SmelterLogic.new()
	SmelterLogic.insert(s, "coal", 4, RULES)
	SmelterLogic.insert(s, "iron_ore", 8, RULES)
	SmelterLogic.step(s, 1000, RULES)
	eq(s.out, RULES.maxOut)
	eq(s.ore, 8 - RULES.maxOut)
	eq(SmelterLogic.takeOutput(s, 1), 1)
	SmelterLogic.step(s, 3, RULES)
	eq(s.out, RULES.maxOut)
end)
test("does not bank progress while it cannot work", function()
	local s = SmelterLogic.new()
	SmelterLogic.insert(s, "iron_ore", 1, RULES)
	SmelterLogic.step(s, 50, RULES)
	SmelterLogic.insert(s, "coal", 1, RULES)
	SmelterLogic.step(s, 0.2, RULES)
	eq(s.out, 0, "ingots right after fuel arrives")
end)
test("refuses what does not fit and what it does not know", function()
	local s = SmelterLogic.new()
	eq(SmelterLogic.insert(s, "coal", 99, RULES), 4)
	eq(SmelterLogic.insert(s, "coal", 1, RULES), 0)
	eq(SmelterLogic.insert(s, "iron_ore", 99, RULES), 8)
	eq(SmelterLogic.insert(s, "iron_ingot", 1, RULES), 0)
	eq(SmelterLogic.insert(s, "banana", 1, RULES), 0)
end)
test("sanitize clamps stored state", function()
	local s = SmelterLogic.sanitize({ fuel = 999, ore = -4, out = 2.7, progress = 55 }, RULES)
	eq(s.fuel, 16)
	eq(s.ore, 0)
	eq(s.out, 2)
	eq(s.progress, 0)
	eq(SmelterLogic.sanitize(nil, RULES).fuel, 0)
	eq(SmelterLogic.sanitize({ fuel = 0 / 0 }, RULES).fuel, 0)
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
		machines = { { id = "smelter", x = 1, y = 1, z = -2, d = 3, s = { fuel = 4, ore = 2, out = 0 } } },
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
	local ids = { "grass", "dirt", "stone", "planks", "metal" }
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
test("every palette and hotbar entry is something that can be placed", function()
	for _, id in Defs.Palette do
		assert(Defs.isPlaceable(id), id .. " is in the palette but is not placeable")
	end
	for _, id in Defs.DefaultHotbar do
		assert(Defs.isPlaceable(id), id .. " is on the hotbar but is not placeable")
	end
	eq(#Defs.DefaultHotbar, 9)
end)
test("machines only refer to items that exist", function()
	for id, def in Defs.Machines do
		if def.item then
			assert(Defs.isItem(def.item), id .. " makes unknown item " .. def.item)
		end
	end
end)
test("a block id is never also a machine or item id", function()
	for id in Defs.Blocks do
		assert(not Defs.isMachine(id) and not Defs.isItem(id), id .. " is used twice")
	end
	for id in Defs.Machines do
		assert(not Defs.isItem(id), id .. " is used twice")
	end
end)

print(string.format("%d passed, %d failed", passed, failed))
if failed > 0 then
	(require("@lune/process") :: any).exit(1)
end
