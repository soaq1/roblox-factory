--!strict
-- Making things by hand: crafting at workbenches, working materials at a hand station, and raising
-- a workbench's tier. Every function either does the whole job or changes nothing.
local CraftLogic = {}

export type Bag = { [string]: number }
-- Which workbenches and hand stations are within reach, and each one's tier.
export type Benches = { [string]: number }
export type Recipe = { out: string, n: number, bench: string, tier: number, ins: Bag }
export type Hand = { station: string, tool: string?, ins: Bag, outs: Bag, fuel: boolean }

CraftLogic.MAX_TIMES = 999
CraftLogic.TOP_TIER = 3
local LIMIT = 2 ^ 31 -- a bag never holds this many of one thing
local WORKBENCHES =
	{ basic = true, tool = true, part = true, machine = true, cook = true, elec = true, furn = true }

local function isTimes(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 1 and n <= CraftLogic.MAX_TIMES
end

-- The tier available for one kind of bench. The bag needs no bench. The unified workbench stands
-- in for all seven workbenches at the top tier.
local function tierOf(benches: Benches, kind: string): number
	if kind == "bag" then
		return math.huge
	end
	if WORKBENCHES[kind] and benches.all then
		return CraftLogic.TOP_TIER
	end
	return benches[kind] or 0
end

local function firstMissing(bag: Bag, ins: Bag, times: number): string?
	local keys = {}
	for key in ins do
		table.insert(keys, key)
	end
	table.sort(keys)
	for _, key in keys do
		if (bag[key] or 0) < ins[key] * times then
			return key
		end
	end
	return nil
end

local function fits(bag: Bag, outs: Bag, times: number): boolean
	for key, n in outs do
		if (bag[key] or 0) + n * times >= LIMIT then
			return false
		end
	end
	return true
end

local function move(bag: Bag, ins: Bag, outs: Bag, times: number)
	for key, n in ins do
		local left = (bag[key] or 0) - n * times
		if left > 0 then
			bag[key] = left
		else
			bag[key] = nil
		end
	end
	for key, n in outs do
		bag[key] = (bag[key] or 0) + n * times
	end
end

-- Why a recipe cannot be made right now, or nil if it can. The second value says which bench,
-- tier or ingredient is the problem.
function CraftLogic.blocked(bag: Bag, recipe: Recipe, benches: Benches, times: any): (string?, any)
	if not isTimes(times) then
		return "times", nil
	end
	local have = tierOf(benches, recipe.bench)
	if have < 1 then
		return "bench", recipe.bench
	elseif have < recipe.tier then
		return "tier", recipe.tier
	end
	local missing = firstMissing(bag, recipe.ins, times)
	if missing then
		return "missing", missing
	end
	if not fits(bag, { [recipe.out] = recipe.n }, times) then
		return "full", recipe.out
	end
	return nil, nil
end

function CraftLogic.craft(bag: Bag, recipe: Recipe, benches: Benches, times: any): (boolean, string?, any)
	local reason, detail = CraftLogic.blocked(bag, recipe, benches, times)
	if reason then
		return false, reason, detail
	end
	move(bag, recipe.ins, { [recipe.out] = recipe.n }, times)
	return true, nil, nil
end

-- Chooses what to burn for `jobs` pieces of work when `banked` jobs' worth of heat is left over
-- from before. The weakest fuel goes first, and nothing the work itself needs is burned.
-- Returns what to burn and the heat left afterwards, or nil if there is not enough.
local function planFuel(
	bag: Bag,
	reserved: Bag,
	values: { [string]: number },
	banked: number,
	jobs: number
): (Bag?, number)
	local need = jobs - banked
	if need <= 0 then
		return {}, banked - jobs
	end
	local keys = {}
	for key in values do
		if (bag[key] or 0) - (reserved[key] or 0) > 0 then
			table.insert(keys, key)
		end
	end
	table.sort(keys, function(a, b)
		if values[a] ~= values[b] then
			return values[a] < values[b]
		end
		return a < b
	end)
	local plan: Bag = {}
	for _, key in keys do
		local spare = (bag[key] or 0) - (reserved[key] or 0)
		local use = math.min(spare, math.ceil(need / values[key]))
		plan[key] = use
		need -= use * values[key]
		if need <= 0 then
			return plan, -need
		end
	end
	return nil, banked
end

-- Works materials by hand at a station, the slow way a machine would otherwise do it.
-- `banked` is heat left from earlier work at a fire; the new amount is the last value returned.
function CraftLogic.hand(
	bag: Bag,
	recipe: Hand,
	benches: Benches,
	times: any,
	fuelValues: { [string]: number },
	banked: number
): (boolean, string?, any, number)
	if not isTimes(times) then
		return false, "times", nil, banked
	end
	if tierOf(benches, recipe.station) < 1 then
		return false, "bench", recipe.station, banked
	end
	if recipe.tool and (bag[recipe.tool] or 0) < 1 then
		return false, "tool", recipe.tool, banked
	end
	local missing = firstMissing(bag, recipe.ins, times)
	if missing then
		return false, "missing", missing, banked
	end
	if not fits(bag, recipe.outs, times) then
		return false, "full", nil, banked
	end
	local burn: Bag, left = {}, banked
	if recipe.fuel then
		local reserved: Bag = {}
		for key, n in recipe.ins do
			reserved[key] = n * times
		end
		local plan, after = planFuel(bag, reserved, fuelValues, banked, times)
		if not plan then
			return false, "fuel", nil, banked
		end
		burn, left = plan, after
	end
	move(bag, burn, {}, 1)
	move(bag, recipe.ins, recipe.outs, times)
	return true, nil, nil, left
end

-- Raises one kind of workbench to its next tier. Tiers belong to the island, not to one placed
-- bench, so moving a bench never loses them.
function CraftLogic.upgrade(
	bag: Bag,
	tiers: { [string]: number },
	benches: Benches,
	kind: any,
	costs: { [string]: Bag }
): (boolean, string?, any)
	if type(kind) ~= "string" or not WORKBENCHES[kind] then
		return false, "kind", nil
	end
	local current = tiers[kind] or 1
	if current >= CraftLogic.TOP_TIER then
		return false, "max", nil
	end
	if not benches[kind] then
		return false, "bench", kind
	end
	local cost = costs[kind .. ":" .. (current + 1)]
	if not cost then
		return false, "max", nil
	end
	local missing = firstMissing(bag, cost, 1)
	if missing then
		return false, "missing", missing
	end
	move(bag, cost, {}, 1)
	tiers[kind] = current + 1
	return true, nil, nil
end

-- Keeps only real bench kinds with a tier from 1 to the top. Used on data read from storage.
function CraftLogic.sanitizeTiers(raw: any): { [string]: number }
	local tiers: { [string]: number } = {}
	if type(raw) == "table" then
		for kind, tier in raw do
			if type(kind) == "string" and WORKBENCHES[kind] and type(tier) == "number" and tier % 1 == 0 then
				if tier >= 2 and tier <= CraftLogic.TOP_TIER then
					tiers[kind] = tier
				end
			end
		end
	end
	return tiers
end

return CraftLogic
