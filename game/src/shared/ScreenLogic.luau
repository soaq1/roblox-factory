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

return ScreenLogic
