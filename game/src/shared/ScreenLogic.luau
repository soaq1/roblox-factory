--!nocheck
-- The parts of the bag, crafting and trade screens that are plain reasoning: what order to list
-- things in, how many times something can be made, which hotbar entry a bag key stands for.
-- Nothing here touches Roblox, and the other modules it needs are passed in as arguments.
local ScreenLogic = {}

-- The order benches are listed in. Anything not named here goes last, alphabetically.
ScreenLogic.BENCH_ORDER =
	{ "bag", "basic", "tool", "part", "machine", "cook", "elec", "furn", "all", "campfire", "hand_furnace" }
ScreenLogic.WORKBENCHES = { "basic", "tool", "part", "machine", "cook", "elec", "furn" }

local function rankOf(order: { string }, name: string): number
	return table.find(order, name) or (#order + 1)
end

-- Groups a list of recipes by one of their fields ("bench" for crafting, "station" for hand work).
-- Each group holds the recipes' positions in the original list, which is what the server is sent.
function ScreenLogic.groups(recipes: { any }, field: string): { { name: string, indexes: { number } } }
	local byName = {}
	local list = {}
	for index, recipe in recipes do
		local name = recipe[field]
		local group = byName[name]
		if not group then
			group = { name = name, indexes = {} }
			byName[name] = group
			table.insert(list, group)
		end
		table.insert(group.indexes, index)
	end
	table.sort(list, function(a, b)
		local ra, rb = rankOf(ScreenLogic.BENCH_ORDER, a.name), rankOf(ScreenLogic.BENCH_ORDER, b.name)
		if ra ~= rb then
			return ra < rb
		end
		return a.name < b.name
	end)
	return list
end

-- How many times a set of ingredients can be paid for out of a bag, up to `cap`.
function ScreenLogic.maxTimes(bag: { [string]: number }, ins: { [string]: number }, cap: number): number
	local times = cap
	for key, n in ins do
		times = math.min(times, math.floor((bag[key] or 0) / n))
	end
	return math.max(times, 0)
end

-- The most times a piece of hand work can be done right now. Fuel and the tool can stop it short
-- of what the ingredients allow, so each candidate is tried on a copy of the bag.
function ScreenLogic.maxHand(CraftLogic, bag, recipe, benches, fuelValues, cap: number): number
	local function works(times: number): boolean
		return (CraftLogic.hand(table.clone(bag), recipe, benches, times, fuelValues, 0))
	end
	local high = ScreenLogic.maxTimes(bag, recipe.ins, cap)
	if high < 1 or not works(1) then
		return 0
	end
	local low = 1
	while low < high do
		local mid = math.ceil((low + high) / 2)
		if works(mid) then
			low = mid
		else
			high = mid - 1
		end
	end
	return low
end

-- Which benches are in reach, from a list of the benches seen and how far each is.
function ScreenLogic.benchesNear(
	seen: { { kind: string, distance: number } },
	tiers: { [string]: number },
	range: number
): { [string]: number }
	local benches = {}
	for _, bench in seen do
		if bench.distance <= range then
			benches[bench.kind] = math.max(benches[bench.kind] or 0, tiers[bench.kind] or 1)
		end
	end
	return benches
end

local function sortedKeys(t): { string }
	local keys = {}
	for key in t do
		table.insert(keys, key)
	end
	table.sort(keys)
	return keys
end

-- What a bag key can be put on the hotbar as: something to place, loose items to drop, or both
-- (a log is a block to build with and an item to feed a sawmill).
function ScreenLogic.forms(Defs, Stock, key: string): { place: string?, drop: string? }
	local forms = {}
	local block = Stock.blockOf(key)
	if block then
		forms.place = block
		return forms
	end
	local machine = Defs.Machines[key]
	if machine then
		-- A planted crop or sapling is never held as itself: it is paid for with its seed.
		if not machine.hidden and not machine.cost then
			forms.place = key
		end
		return forms
	end
	if not Defs.Items[key] then
		return forms
	end
	forms.drop = "item:" .. key
	-- A seed is planted as a crop, a sapling as a tree.
	for _, id in sortedKeys(Defs.Machines) do
		local def = Defs.Machines[id]
		if def.cost == key and not def.hidden then
			forms.place = id
			return forms
		end
	end
	-- An item that is also a block, or that a block is made back from (a clod of dirt).
	if Defs.Blocks[key] then
		forms.place = key
		return forms
	end
	for _, id in sortedKeys(Defs.Blocks) do
		if table.find(Stock.placeCost(id), key) then
			forms.place = id
			return forms
		end
	end
	return forms
end

-- How many of a hotbar entry the bag can supply: loose items for "item:<id>", otherwise everything
-- that can pay for placing it.
function ScreenLogic.held(Defs, Stock, bag: { [string]: number }, entry: string): number
	local item = Defs.itemOf(entry)
	if item then
		return bag[item] or 0
	end
	local total = 0
	local counted = {}
	for _, key in Stock.placeCost(entry) do
		if not counted[key] then
			counted[key] = true
			total += bag[key] or 0
		end
	end
	return total
end

-- 1 for machines, 2 for blocks, 3 for loose items: the order the bag is shown in.
function ScreenLogic.kindRank(Defs, Stock, key: string): number
	if Defs.Machines[key] then
		return 1
	elseif Stock.blockOf(key) then
		return 2
	end
	return 3
end

-- The bag as a list, machines first, then blocks, then items, each by name.
function ScreenLogic.sorted(
	Defs,
	Stock,
	bag: { [string]: number }
): { { key: string, count: number, rank: number } }
	local list = {}
	for key, count in bag do
		table.insert(list, { key = key, count = count, rank = ScreenLogic.kindRank(Defs, Stock, key) })
	end
	table.sort(list, function(a, b)
		if a.rank ~= b.rank then
			return a.rank < b.rank
		end
		local na, nb = Stock.name(a.key), Stock.name(b.key)
		if na ~= nb then
			return na < nb
		end
		return a.key < b.key
	end)
	return list
end

-- How many different things, and how many in all, a bag holds.
function ScreenLogic.totals(bag: { [string]: number }): (number, number)
	local kinds, total = 0, 0
	for _, count in bag do
		kinds += 1
		total += count
	end
	return kinds, total
end

-- A whole number typed into a box, kept between 0 and `max`. Anything unreadable is 0.
function ScreenLogic.amount(text: any, max: number): number
	local n = tonumber(text)
	if not n or n ~= n then
		return 0
	end
	return math.clamp(math.floor(n), 0, math.max(0, math.floor(max)))
end

local function sameOffer(a, b): boolean
	for key, n in a do
		if b[key] ~= n then
			return false
		end
	end
	for key, n in b do
		if a[key] ~= n then
			return false
		end
	end
	return true
end

-- Did the other side change what they put up between two looks at a trade? `me` is "a" or "b".
function ScreenLogic.otherChanged(before, after, me: string): boolean
	if not before or not after then
		return false
	end
	local other = if me == "a" then "b" else "a"
	local was, now = before[other], after[other]
	return was.coins ~= now.coins or not sameOffer(was.offer, now.offer)
end

-- Was I ready before, and un-readied by the other side's change?
function ScreenLogic.wasUnreadied(before, after, me: string): boolean
	if not before or not after then
		return false
	end
	return before[me].ready and not after[me].ready and ScreenLogic.otherChanged(before, after, me)
end

-- ---------------------------------------------------------------------------------------------
-- Screens of different sizes

-- Is this a phone-sized screen? On one, a window takes over the whole screen.
function ScreenLogic.isCompact(viewW: number, viewH: number): boolean
	return viewH < 520 or viewW < 720
end

-- How much to scale a window that was laid out at width by height so that it suits the screen.
-- On a phone it grows or shrinks to fill the screen. Elsewhere it leaves room for the bar below and
-- the read-outs above, never drops under a readable size, and grows with tall screens. A touch
-- screen gets a little extra so buttons are big enough for a finger.
function ScreenLogic.windowScale(
	viewW: number,
	viewH: number,
	width: number,
	height: number,
	touch: boolean
): number
	if viewW <= 0 or viewH <= 0 then
		return 1
	end
	if ScreenLogic.isCompact(viewW, viewH) then
		return math.clamp(math.min(viewW / width, viewH / height), 0.4, 1.6)
	end
	local upper = math.clamp(viewH / 800, 1, 1.6)
	if touch then
		upper = math.max(upper, 1.3)
	end
	return math.clamp(math.min((viewW - 40) / width, (viewH - 200) / height), 0.6, upper)
end

-- The item bar keeps its size in pixels. It shrinks only when the screen is too narrow to hold it
-- with `sideRoom` pixels left free at each end.
function ScreenLogic.barScale(viewW: number, barWidth: number, sideRoom: number): number
	local room = viewW - 2 * sideRoom
	if viewW <= 0 or room >= barWidth then
		return 1
	end
	return math.clamp(room / barWidth, 0.45, 1)
end

-- ---------------------------------------------------------------------------------------------
-- The item bar

-- What a bag gained between two looks at it: every kind whose count went up, by how much, in a
-- steady order.
function ScreenLogic.gains(
	before: { [string]: number },
	after: { [string]: number }
): { { key: string, n: number } }
	local list = {}
	for key, count in after do
		local more = count - (before[key] or 0)
		if more > 0 then
			table.insert(list, { key = key, n = more })
		end
	end
	table.sort(list, function(a, b)
		return a.key < b.key
	end)
	return list
end

-- Adds a gain to the line already showing for that kind if it came within `window` seconds of the
-- last one, and otherwise starts the count again.
function ScreenLogic.mergeGain(
	shown: number?,
	shownAt: number?,
	n: number,
	now: number,
	window: number
): number
	if shown and shownAt and now - shownAt <= window then
		return shown + n
	end
	return n
end

-- The kinds a bag holds now that it did not hold at the last look. `seen` is the set of kinds
-- from that look.
function ScreenLogic.newKinds(seen: { [string]: boolean }, bag: { [string]: number }): { string }
	local fresh = {}
	for key in bag do
		if not seen[key] then
			table.insert(fresh, key)
		end
	end
	table.sort(fresh)
	return fresh
end

-- Puts things onto the bar's empty slots, leaving every slot that already holds something alone.
-- Tools go first, then machines, blocks and items by name. A thing already on the bar in either
-- of its forms is not added again. Returns the new bar and whether anything changed.
function ScreenLogic.fillSlots(
	Defs,
	Stock,
	slots: { string },
	keys: { string },
	isTool: (string) -> boolean
): ({ string }, boolean)
	local bar = table.clone(slots)
	local onBar = {}
	for _, entry in bar do
		onBar[entry] = true
	end
	local order = table.clone(keys)
	table.sort(order, function(a, b)
		local ta, tb = isTool(a), isTool(b)
		if ta ~= tb then
			return ta
		end
		local ra, rb = ScreenLogic.kindRank(Defs, Stock, a), ScreenLogic.kindRank(Defs, Stock, b)
		if ra ~= rb then
			return ra < rb
		end
		local na, nb = Stock.name(a), Stock.name(b)
		if na ~= nb then
			return na < nb
		end
		return a < b
	end)
	local changed = false
	for _, key in order do
		local forms = ScreenLogic.forms(Defs, Stock, key)
		local entry = forms.place or forms.drop
		local there = (forms.place and onBar[forms.place]) or (forms.drop and onBar[forms.drop])
		if entry and not there then
			local free = table.find(bar, "")
			if not free then
				break
			end
			bar[free] = entry
			onBar[entry] = true
			changed = true
		end
	end
	return bar, changed
end

-- The bar with two slots exchanged.
function ScreenLogic.swapSlots(slots: { string }, a: number, b: number): { string }
	local bar = table.clone(slots)
	if bar[a] ~= nil and bar[b] ~= nil then
		bar[a], bar[b] = bar[b], bar[a]
	end
	return bar
end

-- ---------------------------------------------------------------------------------------------
-- Finding things

ScreenLogic.BAG_TABS = { "all", "machine", "block", "tool", "item" }

-- Which tab of the bag a thing belongs under.
function ScreenLogic.bagTab(Defs, Stock, key: string, isTool: (string) -> boolean): string
	if Defs.Machines[key] then
		return "machine"
	elseif Stock.blockOf(key) then
		return "block"
	elseif isTool(key) then
		return "tool"
	end
	return "item"
end

-- Does a name match what was typed? Spaces and letter case are ignored, and nothing typed
-- matches everything.
function ScreenLogic.matches(name: string, query: any): boolean
	if type(query) ~= "string" then
		return true
	end
	local wanted = string.lower((string.gsub(query, "%s", "")))
	if wanted == "" then
		return true
	end
	local given = string.lower((string.gsub(name, "%s", "")))
	return string.find(given, wanted, 1, true) ~= nil
end

-- The craft recipes that can be made once right now, by position in the list.
function ScreenLogic.makeable(CraftLogic, recipes: { any }, bag, benches): { number }
	local list = {}
	for index, recipe in recipes do
		if not CraftLogic.blocked(bag, recipe, benches, 1) then
			table.insert(list, index)
		end
	end
	return list
end

-- The same for hand work. Each is tried on a copy of the bag, because fuel and tools decide too.
function ScreenLogic.makeableHand(CraftLogic, recipes: { any }, bag, benches, fuelValues): { number }
	local list = {}
	for index, recipe in recipes do
		if CraftLogic.hand(table.clone(bag), recipe, benches, 1, fuelValues, 0) then
			table.insert(list, index)
		end
	end
	return list
end

-- The bag keys that one tile stands for. A palette entry and a bag key name things differently
-- ("item:log" and "log", "planks" and "block:planks"), and a thing that is both a block and an
-- item has two keys.
function ScreenLogic.keysOf(Defs, Stock, entry: string): { string }
	local keys = {}
	local function add(key: string)
		if not table.find(keys, key) then
			table.insert(keys, key)
		end
	end
	local item = Defs.itemOf(entry)
	if item then
		add(item)
	elseif Stock.blockOf(entry) or Defs.Machines[entry] then
		add(entry) -- already a bag key
	else
		if Defs.Blocks[entry] then
			add("block:" .. entry)
		end
		if Defs.Items[entry] then
			add(entry)
		end
	end
	return keys
end

-- Everything known about how the things in `keys` are made and what they are used in.
-- Each line is { kind, ins, outs } plus what that kind needs to be shown:
--   craft: index, bench, tier        hand: index, station, tool
--   machine: machine, secs           extractor: machine           upgrade: bench, tier
function ScreenLogic.lookup(Defs, Recipes, keys: { string }): { made: { any }, used: { any }, fuel: number? }
	local wanted = {}
	for _, key in keys do
		wanted[key] = true
	end
	local function touches(bag): boolean
		for key in bag do
			if wanted[key] then
				return true
			end
		end
		return false
	end
	local made, used = {}, {}

	for index, recipe in Recipes.craft do
		local line = {
			kind = "craft",
			index = index,
			bench = recipe.bench,
			tier = recipe.tier,
			ins = recipe.ins,
			outs = { [recipe.out] = recipe.n },
		}
		if wanted[recipe.out] then
			table.insert(made, line)
		end
		if touches(recipe.ins) then
			table.insert(used, line)
		end
	end
	for index, recipe in Recipes.hand do
		local line = {
			kind = "hand",
			index = index,
			station = recipe.station,
			tool = recipe.tool,
			ins = recipe.ins,
			outs = recipe.outs,
		}
		if touches(recipe.outs) then
			table.insert(made, line)
		end
		if touches(recipe.ins) or (recipe.tool and wanted[recipe.tool]) then
			table.insert(used, line)
		end
	end
	for _, machine in sortedKeys(Recipes.byMachine) do
		for _, recipe in Recipes.byMachine[machine] do
			local line = {
				kind = "machine",
				machine = machine,
				secs = recipe.secs,
				ins = recipe.ins,
				outs = recipe.outs,
			}
			if touches(recipe.outs) then
				table.insert(made, line)
			end
			if touches(recipe.ins) then
				table.insert(used, line)
			end
		end
	end
	for _, machine in sortedKeys(Defs.Machines) do
		local def = Defs.Machines[machine]
		if def.behavior == "extractor" and wanted[def.item] and not def.hidden then
			table.insert(made, { kind = "extractor", machine = machine, ins = {}, outs = { [def.item] = 1 } })
		end
	end
	for _, name in sortedKeys(Recipes.upgrades) do
		local cost = Recipes.upgrades[name]
		if touches(cost) then
			local bench, tier = string.match(name, "^(%a+):(%d)$")
			table.insert(
				used,
				{ kind = "upgrade", bench = bench, tier = tonumber(tier), ins = cost, outs = {} }
			)
		end
	end

	local fuel: number? = nil
	for _, key in keys do
		fuel = fuel or Recipes.fuel[key]
	end
	return { made = made, used = used, fuel = fuel }
end

return ScreenLogic
