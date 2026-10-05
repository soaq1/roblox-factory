--!strict
-- Grid maths. Plain numbers only, so it runs outside Roblox for tests.
local Grid = {}

-- Direction index -> step on the X and Z axes. 0 = +X, 1 = +Z, 2 = -X, 3 = -Z.
local DIRS = { { 1, 0 }, { 0, 1 }, { -1, 0 }, { 0, -1 } }

function Grid.key(x: number, y: number, z: number): string
	-- Adding zero turns negative zero into zero, so "-0" can never name a second copy of a cell.
	return (x + 0) .. "," .. (y + 0) .. "," .. (z + 0)
end

function Grid.parseKey(key: string): (number?, number?, number?)
	local xs, ys, zs = string.match(key, "^(-?%d+),(-?%d+),(-?%d+)$")
	if not xs then
		return nil, nil, nil
	end
	return tonumber(xs), tonumber(ys), tonumber(zs)
end

function Grid.isDir(d: any): boolean
	return d == 0 or d == 1 or d == 2 or d == 3
end

function Grid.rotate(d: number, turns: number): number
	return (d + turns) % 4
end

function Grid.dirVec(d: number): (number, number)
	local v = DIRS[d % 4 + 1]
	return v[1], v[2]
end

function Grid.isInt(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and math.abs(n) < 2 ^ 31
end

function Grid.inBounds(x: number, y: number, z: number, max: number): boolean
	return math.abs(x) <= max and math.abs(y) <= max and math.abs(z) <= max
end

-- World position -> the cell that contains it. Cells are centred on multiples of `cell`.
function Grid.toCell(p: number, origin: number, cell: number): number
	return math.floor((p - origin) / cell + 0.5)
end

function Grid.toWorld(c: number, origin: number, cell: number): number
	return origin + c * cell
end

-- The cells a machine of sx by sz cells covers when its anchor is at (x, z) and it faces `dir`.
-- The anchor is the machine's back-left cell; turning the machine swings the rest around it.
function Grid.footprint(x: number, z: number, dir: number, sx: number, sz: number): { { number } }
	local fx, fz = Grid.dirVec(dir)
	local rx, rz = Grid.dirVec(dir + 1)
	local cells = {}
	for i = 0, sx - 1 do
		for j = 0, sz - 1 do
			table.insert(cells, { x + i * fx + j * rx, z + i * fz + j * rz })
		end
	end
	return cells
end

-- Offset, in cells, from the anchor cell's centre to the centre of the whole footprint.
function Grid.footprintCentre(dir: number, sx: number, sz: number): (number, number)
	local fx, fz = Grid.dirVec(dir)
	local rx, rz = Grid.dirVec(dir + 1)
	local i, j = (sx - 1) / 2, (sz - 1) / 2
	return i * fx + j * rx, i * fz + j * rz
end

return Grid
