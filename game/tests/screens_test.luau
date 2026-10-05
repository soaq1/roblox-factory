-- The reasoning behind the bag, crafting and trade screens:  lune run tests/screens_test.luau
local T = require("./harness")
local Defs = require("../src/shared/Defs")
local Recipes = require("../src/shared/Recipes")
local CraftLogic = require("../src/shared/CraftLogic")
local Stock = (require("../src/shared/Stock") :: any)(Defs)
local ScreenLogic = require("../src/shared/ScreenLogic")

local test, eq = T.test, T.eq

test("craft recipes are grouped by bench, bag first, and every recipe is in exactly one group", function()
	local groups = ScreenLogic.groups(Recipes.craft, "bench")
	eq(groups[1].name, "bag")
	local seen, count = {}, 0
	for _, group in groups do
		assert(#group.indexes > 0, "empty group " .. group.name)
		for _, index in group.indexes do
			assert(not seen[index], "recipe listed twice")
			seen[index] = true
			count += 1
			eq(Recipes.craft[index].bench, group.name)
		end
	end
	eq(count, #Recipes.craft)
end)
test("groups keep the recipes' own order and put known benches before unknown ones", function()
	local groups = ScreenLogic.groups({
		{ bench = "zzz" },
		{ bench = "machine" },
		{ bench = "bag" },
		{ bench = "machine" },
		{ bench = "aaa" },
	}, "bench")
	eq(groups[1].name, "bag")
	eq(groups[2].name, "machine")
	eq(groups[2].indexes[1], 2)
	eq(groups[2].indexes[2], 4)
	eq(groups[3].name, "aaa")
	eq(groups[4].name, "zzz")
end)
test("hand work is grouped by station", function()
	local groups = ScreenLogic.groups(Recipes.hand, "station")
	local count = 0
	for _, group in groups do
		for _, index in group.indexes do
			eq(Recipes.hand[index].station, group.name)
			count += 1
		end
	end
	eq(count, #Recipes.hand)
end)

test("the most times something can be made is set by the scarcest ingredient", function()
	eq(ScreenLogic.maxTimes({ plate_fe = 9, rod_fe = 5 }, { plate_fe = 2, rod_fe = 2 }, 999), 2)
	eq(ScreenLogic.maxTimes({ plate_fe = 9 }, { plate_fe = 2, rod_fe = 2 }, 999), 0)
	eq(ScreenLogic.maxTimes({ plank = 100000 }, { plank = 8 }, 999), 999)
	eq(ScreenLogic.maxTimes({}, {}, 5), 5)
end)
test("the most that can be made really can be made, and one more cannot", function()
	local benches = { part = 1 }
	for _, recipe in Recipes.craft do
		if recipe.bench == "part" and recipe.tier <= 1 then
			local bag = {}
			for key, n in recipe.ins do
				bag[key] = n * 3 + 1
			end
			local most = ScreenLogic.maxTimes(bag, recipe.ins, CraftLogic.MAX_TIMES)
			eq(most, 3)
			eq(CraftLogic.blocked(bag, recipe, benches, most), nil)
			eq(CraftLogic.blocked(bag, recipe, benches, most + 1), "missing")
		end
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
test("hand work is limited by fuel as well as by ingredients", function()
	local benches = { hand_furnace = 1 }
	-- one coal pays for four smelts
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10, coal = 1 }, handSmelt(), benches, Recipes.fuel, 999), 4)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 3, coal = 5 }, handSmelt(), benches, Recipes.fuel, 999), 3)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10 }, handSmelt(), benches, Recipes.fuel, 999), 0)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10, coal = 9 }, handSmelt(), {}, Recipes.fuel, 999), 0)
end)
test("working out the most hand work never changes the bag", function()
	local bag = { ore_fe = 10, coal = 2 }
	ScreenLogic.maxHand(CraftLogic, bag, handSmelt(), { hand_furnace = 1 }, Recipes.fuel, 999)
	eq(bag.ore_fe, 10)
	eq(bag.coal, 2)
	eq(bag.ingot_fe, nil)
end)
test("the most hand work is exact: it works, and one more does not", function()
	local benches = { hand_furnace = 1 }
	for _, coal in { 1, 2, 3, 7 } do
		local bag = { ore_fe = 50, coal = coal, log = 3 }
		local most = ScreenLogic.maxHand(CraftLogic, bag, handSmelt(), benches, Recipes.fuel, 999)
		eq((CraftLogic.hand(table.clone(bag), handSmelt(), benches, most, Recipes.fuel, 0)), true)
		eq((CraftLogic.hand(table.clone(bag), handSmelt(), benches, most + 1, Recipes.fuel, 0)), false)
	end
end)

test("benches count only within range, at the island's tier for that kind", function()
	local seen = {
		{ kind = "basic", distance = 4 },
		{ kind = "machine", distance = 15 },
		{ kind = "part", distance = 15.1 },
		{ kind = "hand_furnace", distance = 2 },
		{ kind = "basic", distance = 30 },
	}
	local benches = ScreenLogic.benchesNear(seen, { basic = 3, part = 2 }, 15)
	eq(benches.basic, 3)
	eq(benches.machine, 1)
	eq(benches.part, nil)
	eq(benches.hand_furnace, 1)
	eq(next(ScreenLogic.benchesNear({}, {}, 15)), nil)
end)

test("a bag key becomes the right thing on the hotbar", function()
	local smelter = ScreenLogic.forms(Defs, Stock, "smelter")
	eq(smelter.place, "smelter")
	eq(smelter.drop, nil)
	local planks = ScreenLogic.forms(Defs, Stock, "block:planks")
	eq(planks.place, "planks")
	eq(planks.drop, nil)
	local ingot = ScreenLogic.forms(Defs, Stock, "ingot_fe")
	eq(ingot.place, nil)
	eq(ingot.drop, "item:ingot_fe")
	-- a log is both a block and a thing to feed a sawmill
	local log = ScreenLogic.forms(Defs, Stock, "log")
	eq(log.place, "log")
	eq(log.drop, "item:log")
	eq(ScreenLogic.forms(Defs, Stock, "sapling").place, "plant_sapling")
	eq(ScreenLogic.forms(Defs, Stock, "seed").place, "crop_wheat_1")
	eq(ScreenLogic.forms(Defs, Stock, "dirt_clod").place, "dirt")
	local nothing = ScreenLogic.forms(Defs, Stock, "banana")
	eq(nothing.place, nil)
	eq(nothing.drop, nil)
end)
test("whatever the bag screen offers to place, the bag key can pay for", function()
	local keys = {}
	for id in Defs.Items do
		table.insert(keys, id)
	end
	for id in Defs.Machines do
		table.insert(keys, id)
	end
	for id in Defs.Blocks do
		table.insert(keys, "block:" .. id)
	end
	for _, key in keys do
		local forms = ScreenLogic.forms(Defs, Stock, key)
		if forms.place then
			assert(Defs.isPlaceable(forms.place), key .. " offers unplaceable " .. forms.place)
			assert(table.find(Stock.placeCost(forms.place), key), key .. " cannot pay for " .. forms.place)
			assert(
				not Defs.Machines[forms.place] or not Defs.Machines[forms.place].hidden,
				key .. " offers a hidden machine"
			)
		end
		if forms.drop then
			assert(Defs.itemOf(forms.drop) == key, key .. " drops as the wrong thing")
		end
		-- Hidden machines and planted forms are never held as themselves.
		local machine = Defs.Machines[key]
		local neverHeld = machine and (machine.hidden or machine.cost)
		assert(neverHeld or forms.place or forms.drop, key .. " cannot be used at all")
	end
end)

test("the hotbar count adds up everything that can pay for the slot", function()
	local bag = { log = 3, ["block:log"] = 2, sapling = 4, smelter = 1, dirt_clod = 6 }
	eq(ScreenLogic.held(Defs, Stock, bag, "log"), 5)
	eq(ScreenLogic.held(Defs, Stock, bag, "item:log"), 3)
	eq(ScreenLogic.held(Defs, Stock, bag, "plant_sapling"), 4)
	eq(ScreenLogic.held(Defs, Stock, bag, "smelter"), 1)
	eq(ScreenLogic.held(Defs, Stock, bag, "dirt"), 6)
	eq(ScreenLogic.held(Defs, Stock, bag, "belt"), 0)
	eq(ScreenLogic.held(Defs, Stock, bag, "banana"), 0)
end)

test("the bag is listed machines first, then blocks, then items", function()
	local list = ScreenLogic.sorted(
		Defs,
		Stock,
		{ ingot_fe = 4, ["block:planks"] = 2, smelter = 1, coal = 9, belt = 3 }
	)
	eq(#list, 5)
	eq(list[1].rank, 1)
	eq(list[2].rank, 1)
	eq(list[3].key, "block:planks")
	eq(list[4].rank, 3)
	eq(list[5].rank, 3)
	local kinds, total = ScreenLogic.totals({ ingot_fe = 4, coal = 9 })
	eq(kinds, 2)
	eq(total, 13)
end)
test("the bag's order does not depend on the order it was filled in", function()
	local a = ScreenLogic.sorted(Defs, Stock, { ingot_fe = 1, coal = 1, ore_fe = 1, log = 1 })
	local b = ScreenLogic.sorted(Defs, Stock, { log = 1, ore_fe = 1, coal = 1, ingot_fe = 1 })
	for i = 1, 4 do
		eq(a[i].key, b[i].key)
	end
end)

test("typed amounts are whole numbers within what is held", function()
	eq(ScreenLogic.amount("12", 50), 12)
	eq(ScreenLogic.amount("120", 50), 50)
	eq(ScreenLogic.amount("", 50), 0)
	eq(ScreenLogic.amount("abc", 50), 0)
	eq(ScreenLogic.amount("-3", 50), 0)
	eq(ScreenLogic.amount("2.9", 50), 2)
	eq(ScreenLogic.amount("nan", 50), 0)
	eq(ScreenLogic.amount(7, 5), 5)
	eq(ScreenLogic.amount(nil, 5), 0)
	eq(ScreenLogic.amount("4", -1), 0)
end)

local function snap(aOffer, aCoins, aReady, bOffer, bCoins, bReady)
	return {
		a = { offer = aOffer, coins = aCoins, ready = aReady },
		b = { offer = bOffer, coins = bCoins, ready = bReady },
	}
end
test("a change by the other side is noticed, a change of my own is not", function()
	local before = snap({ ingot_fe = 4 }, 0, true, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.otherChanged(before, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), true)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 5, false), "a"),
		true
	)
	eq(
		ScreenLogic.otherChanged(
			before,
			snap({ ingot_fe = 4 }, 0, false, { core_fe = 1, coal = 1 }, 0, false),
			"a"
		),
		true
	)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "a"),
		false
	)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "b"),
		true
	)
	eq(ScreenLogic.otherChanged(nil, before, "a"), false)
end)
test("being un-readied is reported only when I was ready and the other side changed", function()
	local before = snap({ ingot_fe = 4 }, 0, true, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), true)
	-- I changed my own offer: nothing to warn me about
	eq(
		ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "a"),
		false
	)
	-- I was not ready anyway
	local idle = snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.wasUnreadied(idle, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), false)
	-- I un-readied myself
	eq(
		ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 0, true), "a"),
		false
	)
end)

-- Screens of different sizes
test("a phone counts as a small screen, a tablet and a desktop do not", function()
	eq(ScreenLogic.isCompact(844, 390), true)
	eq(ScreenLogic.isCompact(390, 844), true)
	eq(ScreenLogic.isCompact(1024, 768), false)
	eq(ScreenLogic.isCompact(1920, 1080), false)
end)
test("a window fills a phone screen without spilling over it", function()
	for _, size in { { 760, 470 }, { 860, 520 }, { 420, 300 }, { 620, 300 } } do
		local scale = ScreenLogic.windowScale(844, 354, size[1], size[2], true)
		assert(
			size[1] * scale <= 844 + 0.01 and size[2] * scale <= 354 + 0.01,
			"window spills over a phone screen"
		)
		assert(scale >= 0.4, "window scaled to nothing")
	end
	-- a window laid out small for phones is drawn larger than life, which is what makes it readable
	assert(ScreenLogic.windowScale(844, 354, 620, 300, true) > 1, "a phone layout should be scaled up")
end)
test("on a desktop a window keeps its size, and grows on a tall screen", function()
	eq(ScreenLogic.windowScale(1366, 768, 760, 470, false), 1)
	assert(ScreenLogic.windowScale(1920, 1080, 760, 470, false) > 1.2, "should grow at 1080p")
	assert(ScreenLogic.windowScale(3840, 2160, 760, 470, false) <= 1.6, "should not grow without limit")
	-- and never spills over a small desktop window
	local scale = ScreenLogic.windowScale(900, 600, 860, 520, false)
	assert(860 * scale <= 900 and 520 * scale <= 600, "window spills over a small desktop window")
	eq(ScreenLogic.windowScale(0, 0, 760, 470, false), 1)
end)
test("a touch tablet gets larger windows than a desktop of the same size", function()
	assert(
		ScreenLogic.windowScale(1024, 768, 760, 470, true)
			> ScreenLogic.windowScale(1024, 768, 760, 470, false),
		"touch should scale up"
	)
end)
test("the item bar keeps its size unless the screen is too narrow for it", function()
	eq(ScreenLogic.barScale(1920, 720, 8), 1)
	eq(ScreenLogic.barScale(736, 720, 8), 1)
	local narrow = ScreenLogic.barScale(600, 720, 8)
	assert(narrow < 1 and narrow * 720 <= 600 - 16 + 0.01, "bar should shrink to fit")
	-- a phone leaves room at the sides for the thumbstick and the jump button
	assert(ScreenLogic.barScale(844, 720, 130) < 1, "bar should shrink between the phone controls")
	assert(ScreenLogic.barScale(200, 720, 8) >= 0.45, "bar should not shrink to nothing")
	eq(ScreenLogic.barScale(0, 720, 8), 1)
end)

-- The item bar
local ToolLogic = require("../src/shared/ToolLogic")
local function isTool(key: string): boolean
	return (ToolLogic.parse(key)) ~= nil
end
local function emptyBar(): { string }
	return table.create(10, "")
end
test("a gain is every count that went up, and nothing that went down or stayed", function()
	local list = ScreenLogic.gains(
		{ log = 3, stone = 5, coal = 2 },
		{ log = 5, stone = 4, coal = 2, plank = 8 }
	)
	eq(#list, 2)
	eq(list[1].key, "log")
	eq(list[1].n, 2)
	eq(list[2].key, "plank")
	eq(list[2].n, 8)
	eq(#ScreenLogic.gains({ log = 3 }, { log = 3 }), 0)
	eq(#ScreenLogic.gains({ log = 3 }, {}), 0)
end)
test("gains of one kind within a second add up, later ones start again", function()
	eq(ScreenLogic.mergeGain(nil, nil, 2, 10, 1), 2)
	eq(ScreenLogic.mergeGain(2, 10, 3, 10.6, 1), 5)
	eq(ScreenLogic.mergeGain(5, 10.6, 1, 12, 1), 1)
end)
test("only kinds the bag did not hold before count as new", function()
	local fresh = ScreenLogic.newKinds({ log = true }, { log = 9, stone = 1, pick_wood = 1 })
	eq(#fresh, 2)
	eq(fresh[1], "pick_wood")
	eq(fresh[2], "stone")
	eq(#ScreenLogic.newKinds({ log = true }, { log = 50 }), 0)
end)
test("with nothing on the bar, tools take the first slots", function()
	local bar = ScreenLogic.fillSlots(
		Defs,
		Stock,
		emptyBar(),
		{ "smelter", "log", "pick_wood", "axe_iron", "ingot_fe" },
		isTool
	)
	assert(isTool(Defs.itemOf(bar[1]) :: string), "slot 1 should hold a tool, got " .. bar[1])
	assert(isTool(Defs.itemOf(bar[2]) :: string), "slot 2 should hold a tool, got " .. bar[2])
	eq(bar[3], "smelter")
	eq(bar[6], "")
end)
test("a new thing takes the first empty slot and nothing already placed moves", function()
	local bar = emptyBar()
	bar[1], bar[3], bar[4] = "item:pick_wood", "belt", "grass"
	local after, changed = ScreenLogic.fillSlots(Defs, Stock, bar, { "ingot_fe" }, isTool)
	eq(changed, true)
	eq(after[1], "item:pick_wood")
	eq(after[2], "item:ingot_fe")
	eq(after[3], "belt")
	eq(after[4], "grass")
	-- the bar handed in is not altered
	eq(bar[2], "")
end)
test("a thing already on the bar in either form is not added again", function()
	local bar = emptyBar()
	bar[1] = "item:log" -- the loose form of something that can also be placed
	local after, changed = ScreenLogic.fillSlots(Defs, Stock, bar, { "log" }, isTool)
	eq(changed, false)
	eq(after[2], "")
	bar[1] = "log"
	after, changed = ScreenLogic.fillSlots(Defs, Stock, bar, { "log" }, isTool)
	eq(changed, false)
end)
test("a full bar takes nothing more", function()
	local bar = {}
	for i = 1, 10 do
		bar[i] = "belt"
	end
	local after, changed = ScreenLogic.fillSlots(Defs, Stock, bar, { "ingot_fe", "pick_wood" }, isTool)
	eq(changed, false)
	eq(#after, 10)
end)
test("two slots swap, and an empty one swaps like any other", function()
	local bar = emptyBar()
	bar[1], bar[2] = "item:pick_wood", "belt"
	local after = ScreenLogic.swapSlots(bar, 1, 2)
	eq(after[1], "belt")
	eq(after[2], "item:pick_wood")
	after = ScreenLogic.swapSlots(bar, 1, 7)
	eq(after[1], "")
	eq(after[7], "item:pick_wood")
	eq(bar[1], "item:pick_wood")
	-- a slot that does not exist changes nothing
	eq(ScreenLogic.swapSlots(bar, 1, 11)[1], "item:pick_wood")
end)

-- Finding things
test("each thing in a bag falls under one tab", function()
	eq(ScreenLogic.bagTab(Defs, Stock, "smelter", isTool), "machine")
	eq(ScreenLogic.bagTab(Defs, Stock, "block:planks", isTool), "block")
	eq(ScreenLogic.bagTab(Defs, Stock, "pick_wood", isTool), "tool")
	eq(ScreenLogic.bagTab(Defs, Stock, "ingot_fe", isTool), "item")
	for _, tab in { "machine", "block", "tool", "item" } do
		assert(table.find(ScreenLogic.BAG_TABS, tab), "tab " .. tab .. " is not listed")
	end
end)
test("a search ignores spaces and case, and an empty search matches everything", function()
	eq(ScreenLogic.matches("철 주괴", "철주"), true)
	eq(ScreenLogic.matches("철 주괴", " 주괴 "), true)
	eq(ScreenLogic.matches("철 주괴", "구리"), false)
	eq(ScreenLogic.matches("Belt", "bel"), true)
	eq(ScreenLogic.matches("anything", ""), true)
	eq(ScreenLogic.matches("anything", "   "), true)
	eq(ScreenLogic.matches("anything", nil), true)
	-- what is typed is plain text, never a pattern
	eq(ScreenLogic.matches("a.b", "."), true)
	eq(ScreenLogic.matches("abc", "."), false)
	eq(ScreenLogic.matches("abc", "%a"), false)
end)
test("only what can be made right now is listed as makeable", function()
	local list = ScreenLogic.makeable(CraftLogic, Recipes.craft, { plank = 8 }, {})
	assert(#list > 0, "planks should make something in the bag")
	for _, index in list do
		local recipe = Recipes.craft[index]
		eq(recipe.bench, "bag")
		eq(CraftLogic.blocked({ plank = 8 }, recipe, {}, 1), nil)
	end
	eq(#ScreenLogic.makeable(CraftLogic, Recipes.craft, {}, {}), 0)
	-- standing at a bench opens up more
	local rich = { plank = 999, stone = 999, ingot_fe = 999 }
	assert(
		#ScreenLogic.makeable(CraftLogic, Recipes.craft, rich, { basic = 1 })
			> #ScreenLogic.makeable(CraftLogic, Recipes.craft, rich, {}),
		"a bench in reach should allow more recipes"
	)
end)
test("makeable hand work leaves the bag as it was", function()
	local bag = { log = 4 }
	local list = ScreenLogic.makeableHand(CraftLogic, Recipes.hand, bag, {}, Recipes.fuel)
	assert(#list > 0, "a log should be workable by hand somewhere")
	eq(bag.log, 4)
	for _, index in list do
		eq(Recipes.hand[index].station, "bag")
	end
	eq(#ScreenLogic.makeableHand(CraftLogic, Recipes.hand, {}, {}, Recipes.fuel), 0)
end)
test("a tile's entry is turned into the bag keys it stands for", function()
	eq(ScreenLogic.keysOf(Defs, Stock, "item:ingot_fe")[1], "ingot_fe")
	eq(ScreenLogic.keysOf(Defs, Stock, "ingot_fe")[1], "ingot_fe")
	eq(ScreenLogic.keysOf(Defs, Stock, "smelter")[1], "smelter")
	eq(ScreenLogic.keysOf(Defs, Stock, "block:planks")[1], "block:planks")
	eq(ScreenLogic.keysOf(Defs, Stock, "planks")[1], "block:planks")
	-- a log is a block and an item
	local log = ScreenLogic.keysOf(Defs, Stock, "log")
	assert(table.find(log, "log") and table.find(log, "block:log"), "a log should stand for both of its keys")
	eq(#ScreenLogic.keysOf(Defs, Stock, "banana"), 0)
end)
test("looking a thing up finds every recipe that makes it and every one that uses it", function()
	local info = ScreenLogic.lookup(Defs, Recipes, { "ingot_fe" })
	local kinds = {}
	for _, line in info.made do
		kinds[line.kind] = true
		assert(line.outs.ingot_fe, "a line listed as making iron ingots does not")
	end
	assert(kinds.machine and kinds.hand, "iron ingots are made by machine and by hand")
	assert(#info.used > 10, "iron ingots are used in many things")
	for _, line in info.used do
		assert(line.ins.ingot_fe, "a line listed as using iron ingots does not")
	end
	-- every recipe that mentions it is found, no more and no fewer
	local makes, uses = 0, 0
	for _, recipe in Recipes.craft do
		makes += if recipe.out == "ingot_fe" then 1 else 0
		uses += if recipe.ins.ingot_fe then 1 else 0
	end
	for _, recipe in Recipes.hand do
		makes += if recipe.outs.ingot_fe then 1 else 0
		uses += if recipe.ins.ingot_fe then 1 else 0
	end
	for _, list in Recipes.byMachine do
		for _, recipe in list do
			makes += if recipe.outs.ingot_fe then 1 else 0
			uses += if recipe.ins.ingot_fe then 1 else 0
		end
	end
	for _, cost in Recipes.upgrades do
		uses += if cost.ingot_fe then 1 else 0
	end
	eq(#info.made, makes)
	eq(#info.used, uses)
end)
test("a lookup knows extractors, fuels, tools and machines", function()
	local ore = ScreenLogic.lookup(Defs, Recipes, { "ore_fe" })
	local fromExtractor = false
	for _, line in ore.made do
		fromExtractor = fromExtractor or line.kind == "extractor"
	end
	eq(fromExtractor, true)
	eq(ScreenLogic.lookup(Defs, Recipes, { "coal" }).fuel, Recipes.fuel.coal)
	eq(ScreenLogic.lookup(Defs, Recipes, { "ingot_fe" }).fuel, nil)
	-- a hammer is used by the work it is the tool for
	local hammer = ScreenLogic.lookup(Defs, Recipes, { "hammer" })
	local asTool = false
	for _, line in hammer.used do
		asTool = asTool or (line.kind == "hand" and line.tool == "hammer")
	end
	eq(asTool, true)
	-- a machine is made at a bench
	local smelter = ScreenLogic.lookup(Defs, Recipes, { "smelter" })
	eq(smelter.made[1].kind, "craft")
	-- something unknown has nothing
	local nothing = ScreenLogic.lookup(Defs, Recipes, { "banana" })
	eq(#nothing.made + #nothing.used, 0)
end)

T.done()
