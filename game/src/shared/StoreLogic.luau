--!strict
-- Moving things between two piles, such as a player's bag and a chest. A move either happens in
-- full for the amount it reports or not at all, and nothing is ever made or lost: what leaves one
-- pile is exactly what arrives in the other.
local StoreLogic = {}

export type Pile = { [string]: number }

local LIMIT = 2 ^ 31 -- a pile never holds this many of one thing

local function isAmount(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 1 and n < LIMIT
end

-- Moves up to n of one thing from one pile to another: all that was asked for, or all there is if
-- there is less. Returns how many moved (0 if the request made no sense or nothing could move).
function StoreLogic.move(from: Pile, to: Pile, key: any, n: any): number
	if type(key) ~= "string" or not isAmount(n) or from == to then
		return 0
	end
	local moved = math.min(n, from[key] or 0)
	if moved < 1 or (to[key] or 0) + moved >= LIMIT then
		return 0
	end
	local left = (from[key] or 0) - moved
	if left > 0 then
		from[key] = left
	else
		from[key] = nil
	end
	to[key] = (to[key] or 0) + moved
	return moved
end

-- Moves everything from one pile to another, kind by kind. Returns how many things moved.
function StoreLogic.moveAll(from: Pile, to: Pile): number
	local total = 0
	local keys = {}
	for key in from do
		table.insert(keys, key)
	end
	for _, key in keys do
		total += StoreLogic.move(from, to, key, from[key])
	end
	return total
end

-- How many different things, and how many in all.
function StoreLogic.totals(pile: Pile): (number, number)
	local kinds, total = 0, 0
	for _, n in pile do
		kinds += 1
		total += n
	end
	return kinds, total
end

return StoreLogic
