--!strict
-- A bag is a table of item id -> count. Counts are always positive whole numbers.
local Inventory = {}

export type Bag = { [string]: number }

local function isCount(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n > 0 and n < 2 ^ 31
end

function Inventory.count(bag: Bag, id: string): number
	return bag[id] or 0
end

function Inventory.add(bag: Bag, id: string, n: number): boolean
	if not isCount(n) then
		return false
	end
	bag[id] = (bag[id] or 0) + n
	return true
end

function Inventory.remove(bag: Bag, id: string, n: number): boolean
	if not isCount(n) or (bag[id] or 0) < n then
		return false
	end
	if bag[id] == n then
		bag[id] = nil
	else
		bag[id] -= n
	end
	return true
end

-- Keeps only known ids with valid counts. Used on data read from storage.
function Inventory.sanitize(raw: any, isKnown: (string) -> boolean): Bag
	local bag: Bag = {}
	if type(raw) ~= "table" then
		return bag
	end
	for id, n in raw do
		if type(id) == "string" and isKnown(id) and isCount(n) then
			bag[id] = n
		end
	end
	return bag
end

return Inventory
