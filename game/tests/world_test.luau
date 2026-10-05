-- Tools, mining and monsters:  lune run tests/world_test.luau
local T = require("./harness")
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

T.done()
