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
test("machines and blocks that are only blocks have no loose form", function()
	eq(HandLogic.looseForm(Defs, Stock, "smelter", { smelter = 1 }, false), nil)
	eq(HandLogic.looseForm(Defs, Stock, "smelter", {}, true), nil)
	eq(HandLogic.looseForm(Defs, Stock, "planks", { ["block:planks"] = 5 }, false), nil)
	eq(HandLogic.looseForm(Defs, Stock, "", {}, true), nil)
end)
test("whatever Q lets go of is a real item", function()
	for _, group in Defs.Palette do
		for _, entry in group.ids do
			local loose = HandLogic.looseForm(Defs, Stock, entry, {}, true)
			assert(
				loose == nil or Defs.isItem(loose),
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

test("every block can be told from every other by how it looks", function()
	for id, def in Defs.Blocks do
		local c, t = def.color, def.top
		local capped = math.abs(t[1] - c[1]) + math.abs(t[2] - c[2]) + math.abs(t[3] - c[3]) > 60
		eq(HandLogic.blockByLook(Defs, c, if capped then t else nil), id)
	end
	eq(HandLogic.blockByLook(Defs, { 1, 2, 3 }, nil), nil)
end)
test("dirt and farmland share a side colour and are told apart by the cap", function()
	local dirt, farm = Defs.Blocks.dirt, Defs.Blocks.farmland
	eq(HandLogic.blockByLook(Defs, dirt.color, nil), "dirt")
	eq(HandLogic.blockByLook(Defs, farm.color, farm.top), "farmland")
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
	eq(HandLogic.beltPorts("open")[2].side, "E")
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

T.done()
