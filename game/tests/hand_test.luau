-- Runs outside Roblox:  lune run tests/hand_test.luau
local T = require("./harness")
local Defs = require("../src/shared/Defs")
local Grid = require("../src/shared/Grid")
local HandLogic = require("../src/shared/HandLogic")
local ToolLogic = require("../src/shared/ToolLogic")
local Stock = (require("../src/shared/Stock") :: any)(Defs)

local test, eq = T.test, T.eq

test("an item entry is let go as that item", function()
	eq(HandLogic.looseForm(Defs, Stock, "item:ingot_fe", {}, false), "ingot_fe")
	eq(HandLogic.looseForm(Defs, Stock, "item:pick_wood", { pick_wood = 1 }, false), "pick_wood")
end)
test("a held block that is also an item is let go as the item", function()
	eq(HandLogic.looseForm(Defs, Stock, "log", { log = 3 }, false), "log")
	eq(HandLogic.looseForm(Defs, Stock, "stone", { stone = 1 }, false), "stone")
	eq(HandLogic.looseForm(Defs, Stock, "dirt", { dirt_clod = 2 }, false), "dirt_clod")
	-- nothing to let go of when the bag has none, unless everything is free
	eq(HandLogic.looseForm(Defs, Stock, "log", {}, false), nil)
	eq(HandLogic.looseForm(Defs, Stock, "log", {}, true), "log")
end)
test("a planted thing is let go as its seed", function()
	eq(HandLogic.looseForm(Defs, Stock, "plant_sapling", { sapling = 1 }, false), "sapling")
	eq(HandLogic.looseForm(Defs, Stock, "crop_wheat_1", { seed = 4 }, false), "seed")
end)
test("a held block that is only a block is let go as the block itself", function()
	eq(HandLogic.looseForm(Defs, Stock, "planks", { ["block:planks"] = 5 }, false), "block:planks")
	eq(HandLogic.looseForm(Defs, Stock, "grass", { ["block:grass"] = 1 }, false), "block:grass")
	eq(HandLogic.looseForm(Defs, Stock, "grass", {}, false), nil)
	eq(HandLogic.looseForm(Defs, Stock, "grass", {}, true), "block:grass")
	-- a block held in both forms goes in the form the bag has; the block form first
	eq(HandLogic.looseForm(Defs, Stock, "stone", { ["block:stone"] = 1, stone = 1 }, false), "block:stone")
	eq(HandLogic.looseForm(Defs, Stock, "stone", {}, true), "stone")
end)
test("every block in the game can be let go of when the bag holds it", function()
	for id in Defs.Blocks do
		local held = {}
		for _, key in Stock.placeCost(id) do
			held[key] = 1
		end
		local loose = HandLogic.looseForm(Defs, Stock, id, held, false)
		assert(loose ~= nil, id .. " cannot be let go of")
		assert(
			Stock.loose(loose) ~= nil,
			id .. " is let go as " .. tostring(loose) .. ", which cannot lie loose"
		)
		assert(Stock.isKey(loose), tostring(loose) .. " would not go back into a bag")
	end
end)
test("what lies loose has a size and a colour, and a machine cannot lie loose", function()
	local item = Stock.loose("ingot_fe")
	eq(item.size[1], Defs.Items.ingot_fe.size[1])
	local block = Stock.loose("block:grass")
	eq(block.size[1], 1.5)
	eq(block.color[2], Defs.Blocks.grass.top[2])
	eq(block.ball, false)
	eq(Stock.loose("smelter"), nil)
	eq(Stock.loose("grass"), nil) -- a block's bag key is "block:grass"
	eq(Stock.loose("block:banana"), nil)
	eq(Stock.loose(nil), nil)
end)
test("machines have no loose form", function()
	eq(HandLogic.looseForm(Defs, Stock, "smelter", { smelter = 1 }, false), nil)
	eq(HandLogic.looseForm(Defs, Stock, "smelter", {}, true), nil)
	eq(HandLogic.looseForm(Defs, Stock, "", {}, true), nil)
end)
test("whatever Q lets go of is something that can lie loose", function()
	for _, group in Defs.Palette do
		for _, entry in group.ids do
			local loose = HandLogic.looseForm(Defs, Stock, entry, {}, true)
			assert(
				loose == nil or Stock.loose(loose) ~= nil,
				entry .. " would be let go as unknown " .. tostring(loose)
			)
		end
	end
end)

test("looking at a thing selects the slot that has it, else loads the current slot", function()
	local slots = { "item:pick_wood", "belt", "", "", "", "", "", "", "", "" }
	local what, index = HandLogic.pick(Stock, slots, "belt", {}, false)
	eq(what, "select")
	eq(index, 2)
	what, index = HandLogic.pick(Stock, slots, "smelter", { smelter = 1 }, false)
	eq(what, "assign")
	eq(index, nil)
	what = HandLogic.pick(Stock, slots, "smelter", {}, false)
	eq(what, "none")
	what = HandLogic.pick(Stock, slots, "smelter", {}, true)
	eq(what, "assign")
	-- a block is supplied by whatever can pay for placing it
	what = HandLogic.pick(Stock, slots, "log", { log = 1 }, false)
	eq(what, "assign")
	what = HandLogic.pick(Stock, slots, "dirt", { dirt_clod = 1 }, false)
	eq(what, "assign")
end)

test("a dragged belt faces the way the drag moves", function()
	for d = 0, 3 do
		local fx, fz = Grid.dirVec(d)
		eq(HandLogic.dragDir(fx, 0, fz), d)
	end
	eq(HandLogic.dragDir(0, 0, 0), nil)
	eq(HandLogic.dragDir(1, 0, 1), nil)
	eq(HandLogic.dragDir(2, 0, 0), nil)
	eq(HandLogic.dragDir(1, 1, 0), nil)
end)

test("a machine's covered cells are its footprint on every layer it keeps", function()
	local keys = HandLogic.covered(Grid, { sx = 2, sz = 2, sy = 2 }, 0, 1, 0, 0)
	eq(#keys, 8)
	assert(table.find(keys, Grid.key(0, 1, 0)), "anchor cell missing")
	assert(table.find(keys, Grid.key(1, 2, 1)), "far upper cell missing")
	eq(#HandLogic.covered(Grid, Defs.Machines.belt, 3, 1, -2, 2), 1)
end)

test("a belt's outline shows it taking in at the back and giving out where it carries", function()
	eq(HandLogic.beltPorts("straight")[2].side, "E")
	eq(HandLogic.beltPorts("right")[2].side, "S")
	eq(HandLogic.beltPorts("left")[2].side, "N")
	eq(HandLogic.beltPorts(nil)[1].side, "W")
	eq(HandLogic.beltPorts(nil)[1].kind, "in")
end)

-- Lifting machines
test("a machine is lifted with a pickaxe, and other tools are slow", function()
	local hard = ToolLogic.machineHardness(Defs.Machines.smelter)
	local pick = ToolLogic.machineHits(hard, { pick_wood = 1 })
	local axe = ToolLogic.machineHits(hard, { axe_dia = 1 })
	assert(pick > 1, "a machine should take more than one swing with a wooden pickaxe")
	assert(axe > pick, "the wrong tool should be slower than the pickaxe")
	eq(axe, ToolLogic.machineHits(hard, {}))
	assert(ToolLogic.machineHits(hard, { pick_dia = 1 }) < pick, "a better pickaxe should be faster")
	eq(ToolLogic.machineHits(1, {}), 1)
end)
test("plants come up in one go, belts faster than big machines", function()
	eq(ToolLogic.machineHardness(Defs.Machines.plant_sapling), 1)
	eq(ToolLogic.machineHardness(Defs.Machines.crop_wheat_1), 1)
	assert(
		ToolLogic.machineHardness(Defs.Machines.belt) < ToolLogic.machineHardness(Defs.Machines.smelter),
		"a belt should be lighter than a smelter"
	)
	for id, def in Defs.Machines do
		assert(ToolLogic.machineHardness(def) >= 1, id .. " has no hardness")
	end
end)

test("a block is not placed where a character stands, but is beside, under and over them", function()
	-- A character standing on the block at cell (0, 0, 0): cells are 3 studs, the block's top is at
	-- 1.5, and the middle of the body is about 3 studs above the feet.
	local rx, ry, rz = 0, 4.54, 0
	local function at(x: number, y: number, z: number): boolean
		return HandLogic.bodyInCell(x * 3, y * 3, z * 3, 3, rx, ry, rz)
	end
	eq(at(0, 1, 0), true) -- the legs
	eq(at(0, 2, 0), true) -- the head
	eq(at(0, 0, 0), false) -- the block stood on
	eq(at(0, 3, 0), false) -- above the head
	eq(at(1, 1, 0), false)
	eq(at(-1, 1, 0), false)
	eq(at(0, 1, 1), false)
	eq(at(0, 2, -1), false)
	-- standing on the line between two cells, the body is in both
	eq(HandLogic.bodyInCell(0, 3, 0, 3, 1.5, 4.54, 0), true)
	eq(HandLogic.bodyInCell(3, 3, 0, 3, 1.5, 4.54, 0), true)
	-- at the top of a jump the cell under the feet is free again
	eq(HandLogic.bodyInCell(0, 3, 0, 3, 0, 4.54 + 3, 0), false)
end)

T.done()
