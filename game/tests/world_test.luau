-- Tools, mining and monsters:  lune run tests/world_test.luau
local T = require("./harness")
local Config = require("../src/shared/Config")
local Defs = require("../src/shared/Defs")
local ToolLogic = require("../src/shared/ToolLogic")

local test, eq = T.test, T.eq

test("every tool a tier and kind can name is a real item", function()
	for _, kind in ToolLogic.KINDS do
		for _, tier in ToolLogic.TIERS do
			assert(Defs.isItem(kind .. "_" .. tier), kind .. "_" .. tier .. " is not an item")
		end
	end
end)
test("the best tool in the bag is the highest tier held", function()
	eq(ToolLogic.best({}, "pick"), 0)
	eq(ToolLogic.best({ pick_wood = 1 }, "pick"), 1)
	local rank, key = ToolLogic.best({ pick_wood = 1, pick_iron = 2, pick_stone = 1 }, "pick")
	eq(rank, 3)
	eq(key, "pick_iron")
	eq(ToolLogic.best({ pick_dia = 1 }, "axe"), 0)
	eq(ToolLogic.best({ pick_dia = 0 }, "pick"), 0)
end)
test("a better tool never makes work slower", function()
	local last = 0
	for rank = 0, #ToolLogic.TIERS do
		local power = ToolLogic.power(rank)
		assert(power > last, "power does not rise at rank " .. rank)
		last = power
	end
	eq(ToolLogic.power(99), ToolLogic.power(#ToolLogic.TIERS))
	eq(ToolLogic.power(-3), ToolLogic.power(0))
end)
test("every block can be broken bare-handed, and the right tool is quicker", function()
	for id in Defs.Blocks do
		local bare = ToolLogic.blockHits(id, {})
		assert(bare >= 1 and bare % 1 == 0, id .. " takes an odd number of swings")
		local tool = ToolLogic.blockTool(id)
		if tool then
			assert(Defs.isItem(tool .. "_wood"), id .. " names unknown tool " .. tool)
			local best = ToolLogic.blockHits(id, { [tool .. "_dia"] = 1 })
			assert(best < bare, id .. " is no quicker with its tool")
			eq(best, 1)
		end
	end
end)
test("the wrong tool is no better than bare hands", function()
	eq(ToolLogic.blockHits("stone", { axe_dia = 1, shovel_dia = 1 }), ToolLogic.blockHits("stone", {}))
	eq(ToolLogic.blockHits("stone", { pick_wood = 1 }), 4)
	eq(ToolLogic.blockHits("stone", {}), 8)
	eq(ToolLogic.blockHits("leaves", {}), 1)
	-- a block nobody listed still breaks
	assert(ToolLogic.blockHits("banana", {}) >= 1)
end)
test("every mine node gives a real item and, if it has one, a real core", function()
	for kind, node in ToolLogic.NODES do
		assert(Defs.isItem(node.item), kind .. " gives unknown item " .. node.item)
		assert(not node.core or Defs.isItem(node.core), kind .. " gives unknown core")
		assert(node.hardness > 0 and node.respawn > 0, kind .. " has a bad number")
		assert(node.minRank >= 0 and node.minRank <= #ToolLogic.TIERS, kind .. " needs an impossible pickaxe")
		local needs = ToolLogic.nodeNeeds(kind)
		assert(not needs or Defs.isItem(needs), kind .. " asks for an unknown pickaxe")
	end
	eq(ToolLogic.NODES.ore_au.core, nil)
	eq(ToolLogic.NODES.ore_dia.core, nil)
end)
test("a new player's pickaxe mines stone, coal, copper and iron but not gold or diamond", function()
	local bag = { pick_wood = 1 }
	for _, kind in { "stone", "coal", "ore_cu", "ore_fe" } do
		assert(ToolLogic.nodeSwing(kind, bag), kind .. " cannot be mined with the first pickaxe")
	end
	eq(ToolLogic.nodeSwing("ore_au", bag), nil)
	eq(ToolLogic.nodeSwing("ore_dia", bag), nil)
	eq(ToolLogic.nodeNeeds("ore_au"), "pick_iron")
	eq(ToolLogic.nodeNeeds("stone"), nil)
	-- stone needs no pickaxe at all, coal does
	assert(ToolLogic.nodeSwing("stone", {}))
	eq(ToolLogic.nodeSwing("coal", {}), nil)
	eq(ToolLogic.nodeSwing("banana", bag), nil)
	assert(ToolLogic.nodeSwing("ore_dia", { pick_steel = 1 }))
end)
test("vein cores are rare, and only from nodes that have one", function()
	eq(ToolLogic.rollCore("ore_fe", 0), "core_fe")
	eq(ToolLogic.rollCore("ore_fe", ToolLogic.CORE_CHANCE), nil)
	eq(ToolLogic.rollCore("ore_fe", 0.99), nil)
	eq(ToolLogic.rollCore("ore_au", 0), nil)
	eq(ToolLogic.rollCore("banana", 0), nil)
	assert(ToolLogic.CORE_CHANCE > 0 and ToolLogic.CORE_CHANCE < 0.2)
end)
test("a better sword hits harder, and bare hands still hurt a little", function()
	local last = 0
	assert(ToolLogic.damage({}) > 0)
	for _, tier in ToolLogic.TIERS do
		local damage = ToolLogic.damage({ ["sword_" .. tier] = 1 })
		assert(damage > last, "sword_" .. tier .. " is no better than the one before")
		last = damage
	end
	eq(ToolLogic.damage({ pick_dia = 1 }), ToolLogic.damage({}))
	eq(ToolLogic.rollPart(0), true)
	eq(ToolLogic.rollPart(0.99), false)
end)
test("swings add up on one target and start over on another", function()
	local swing, hits = ToolLogic.swing(nil, "a", 10, 0.15, 2)
	eq(hits, 1)
	swing, hits = ToolLogic.swing(swing, "a", 10.2, 0.15, 2)
	eq(hits, 2)
	swing, hits = ToolLogic.swing(swing, "b", 10.4, 0.15, 2)
	eq(hits, 1)
	eq(swing.target, "b")
end)
test("a swing that comes too soon is ignored, and a long pause starts over", function()
	local swing, hits = ToolLogic.swing(nil, "a", 10, 0.15, 2)
	swing, hits = ToolLogic.swing(swing, "a", 10.05, 0.15, 2)
	eq(hits, 0)
	eq(swing.hits, 1)
	-- an ignored swing does not push the clock forward either
	swing, hits = ToolLogic.swing(swing, "a", 10.16, 0.15, 2)
	eq(hits, 2)
	swing, hits = ToolLogic.swing(swing, "a", 13, 0.15, 2)
	eq(hits, 1)
end)

test("a tool is told from other items by its name", function()
	local kind, rank = ToolLogic.parse("pick_iron")
	eq(kind, "pick")
	eq(rank, 3)
	eq((ToolLogic.parse("sword_dia")), "sword")
	eq((ToolLogic.parse("ingot_fe")), nil)
	eq((ToolLogic.parse("hammer")), nil)
	eq((ToolLogic.parse("pick_banana")), nil)
	eq((ToolLogic.parse(7)), nil)
	eq((ToolLogic.parse(nil)), nil)
end)
test("only the tool in the hand counts", function()
	local bag = { pick_dia = 1, pick_wood = 1, axe_iron = 1 }
	-- holding the wooden pick, the diamond one in the bag does nothing
	eq(
		ToolLogic.blockHits("stone", ToolLogic.inHand(bag, "pick_wood", false)),
		ToolLogic.blockHits("stone", { pick_wood = 1 })
	)
	-- holding an axe, stone goes as slowly as with the wrong tool
	eq(
		ToolLogic.blockHits("stone", ToolLogic.inHand(bag, "axe_iron", false)),
		ToolLogic.blockHits("stone", {})
	)
	-- a tool that is not owned is not in the hand, unless everything is free
	eq(next(ToolLogic.inHand(bag, "pick_gold", false)), nil)
	eq(next(ToolLogic.inHand(bag, "pick_gold", true)), "pick_gold")
	-- things that are not tools are never "in hand" for this purpose
	eq(next(ToolLogic.inHand({ ingot_fe = 5 }, "ingot_fe", false)), nil)
	eq(next(ToolLogic.inHand(bag, nil, true)), nil)
end)
test("the richer rocks need the right pickaxe in the hand", function()
	local bag = { pick_steel = 1, pick_wood = 1 }
	eq(ToolLogic.nodeSwing("ore_dia", ToolLogic.inHand(bag, "pick_wood", false)), nil)
	assert(
		ToolLogic.nodeSwing("ore_dia", ToolLogic.inHand(bag, "pick_steel", false)),
		"steel pick should mine diamond"
	)
end)

test("tools in a bag are counted, whatever their kind", function()
	eq(ToolLogic.count({}), 0)
	eq(ToolLogic.count({ ingot_fe = 9, hammer = 1 }), 0)
	eq(ToolLogic.count({ pick_wood = 1, axe_iron = 2, log = 5 }), 3)
end)

test("a hoe tills dirt and grass, and nothing else does", function()
	eq(ToolLogic.tills("hoe_wood", "dirt"), true)
	eq(ToolLogic.tills("hoe_dia", "grass"), true)
	eq(ToolLogic.tills("hoe_wood", "stone"), false)
	eq(ToolLogic.tills("hoe_wood", "farmland"), false)
	eq(ToolLogic.tills("shovel_wood", "dirt"), false)
	eq(ToolLogic.tills("pick_wood", "grass"), false)
	eq(ToolLogic.tills(nil, "dirt"), false)
end)

test("a hoe leaves farmland alone, so a long press does not undo the tilling", function()
	eq(ToolLogic.spares("hoe_wood", "farmland"), true)
	eq(ToolLogic.spares("hoe_wood", "dirt"), false)
	eq(ToolLogic.spares("shovel_wood", "farmland"), false)
	eq(ToolLogic.spares(nil, "farmland"), false)
end)

test("an axe is the tool for a tree, as a pickaxe is for a machine", function()
	local axe, pick = { axe_wood = 1 }, { pick_wood = 1 }
	assert(
		ToolLogic.machineHits(12, axe, "axe") < ToolLogic.machineHits(12, pick, "axe"),
		"an axe should fell faster"
	)
	eq(ToolLogic.machineHits(12, pick, "axe"), ToolLogic.machineHits(12, {}, "axe"))
	-- with no tool named, a pickaxe is the one that counts
	eq(ToolLogic.machineHits(8, pick), ToolLogic.machineHits(8, pick, "pick"))
	assert(
		ToolLogic.machineHits(8, pick) < ToolLogic.machineHits(8, axe),
		"a pickaxe should lift a machine faster"
	)
end)

test("a new player starts with a wooden pickaxe and a wooden axe, one of each", function()
	eq(Config.START_ITEMS.pick_wood, 1)
	eq(Config.START_ITEMS.axe_wood, 1)
	for id in Config.START_ITEMS do
		assert(Defs.isItem(id), id .. " is not an item")
	end
	eq(ToolLogic.best(Config.START_ITEMS, "pick"), 1)
	eq(ToolLogic.best(Config.START_ITEMS, "axe"), 1)
	eq(ToolLogic.count(Config.START_ITEMS), 2)
end)

T.done()
