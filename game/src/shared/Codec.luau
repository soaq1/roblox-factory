--!strict
-- Turns an island into a compact table for storage and back.
-- Blocks of one kind that sit in a row along X are stored as one run: x, y, z, length.
local Codec = {}

Codec.VERSION = 1

export type BlockEntry = { x: number, y: number, z: number, id: string }
export type MachineEntry = { id: string, x: number, y: number, z: number, d: number, s: any }
export type Island = { blocks: { BlockEntry }, machines: { MachineEntry }, bag: { [string]: number } }
export type Checks = {
	isBlock: (any) -> boolean,
	isMachine: (any) -> boolean,
	maxCoord: number,
}

local function isInt(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and math.abs(n) < 2 ^ 31
end

function Codec.encode(island: Island): { [string]: any }
	local byId: { [string]: { BlockEntry } } = {}
	for _, b in island.blocks do
		local list = byId[b.id]
		if not list then
			list = {}
			byId[b.id] = list
		end
		table.insert(list, b)
	end

	local blocks: { [string]: { number } } = {}
	for id, list in byId do
		table.sort(list, function(a, b)
			if a.y ~= b.y then
				return a.y < b.y
			elseif a.z ~= b.z then
				return a.z < b.z
			end
			return a.x < b.x
		end)
		local runs: { number } = {}
		local i = 1
		while i <= #list do
			local first = list[i]
			local len = 1
			while
				i + len <= #list
				and list[i + len].y == first.y
				and list[i + len].z == first.z
				and list[i + len].x == first.x + len
			do
				len += 1
			end
			table.insert(runs, first.x)
			table.insert(runs, first.y)
			table.insert(runs, first.z)
			table.insert(runs, len)
			i += len
		end
		blocks[id] = runs
	end

	local machines = {}
	for _, m in island.machines do
		table.insert(machines, { i = m.id, x = m.x, y = m.y, z = m.z, d = m.d, s = m.s })
	end

	return { v = Codec.VERSION, b = blocks, m = machines, g = island.bag }
end

-- Returns the island and how many entries were dropped as unreadable.
-- Returns nil when the data cannot be trusted at all.
function Codec.decode(raw: any, checks: Checks): (Island?, number)
	if type(raw) ~= "table" or raw.v ~= Codec.VERSION then
		return nil, 0
	end
	local skipped = 0
	local island: Island = { blocks = {}, machines = {}, bag = {} }
	local taken: { [string]: boolean } = {}

	if type(raw.b) == "table" then
		for id, runs in raw.b do
			if not checks.isBlock(id) or type(runs) ~= "table" or #runs % 4 ~= 0 then
				skipped += 1
				continue
			end
			for i = 1, #runs, 4 do
				local x, y, z, len = runs[i], runs[i + 1], runs[i + 2], runs[i + 3]
				local ok = isInt(x) and isInt(y) and isInt(z) and isInt(len) and len >= 1
				ok = ok and math.abs(y) <= checks.maxCoord and math.abs(z) <= checks.maxCoord
				ok = ok and math.abs(x) <= checks.maxCoord and math.abs(x + len - 1) <= checks.maxCoord
				if not ok then
					skipped += 1
					continue
				end
				for dx = 0, len - 1 do
					local key = (x + dx) .. "," .. y .. "," .. z
					if taken[key] then
						skipped += 1
					else
						taken[key] = true
						table.insert(island.blocks, { x = x + dx, y = y, z = z, id = id })
					end
				end
			end
		end
	end

	if type(raw.m) == "table" then
		for _, m in raw.m do
			local ok = type(m) == "table" and checks.isMachine(m.i)
			ok = ok and isInt(m.x) and isInt(m.y) and isInt(m.z)
			ok = ok and (m.d == 0 or m.d == 1 or m.d == 2 or m.d == 3)
			ok = ok
				and math.abs(m.x) <= checks.maxCoord
				and math.abs(m.y) <= checks.maxCoord
				and math.abs(m.z) <= checks.maxCoord
			if not ok then
				skipped += 1
				continue
			end
			local key = m.x .. "," .. m.y .. "," .. m.z
			if taken[key] then
				skipped += 1
				continue
			end
			taken[key] = true
			table.insert(island.machines, { id = m.i, x = m.x, y = m.y, z = m.z, d = m.d, s = m.s })
		end
	end

	if type(raw.g) == "table" then
		island.bag = raw.g
	end
	return island, skipped
end

return Codec
