-- Builds the look of a catalogue model out of basic parts. The server uses it for placed machines
-- and the client for the pictures in the palette. The parts are for show only: nothing collides
-- with them and the build cursor ignores them.
local Palette = require(script.Parent:WaitForChild("ModelPalette"))
local models = script.Parent:WaitForChild("Models")

local ModelBuilder = {}

local SHAPES = { [0] = Enum.PartType.Block, [1] = Enum.PartType.Cylinder, [2] = Enum.PartType.Ball }
local STRIDE = 17 -- numbers per part, see the header of any file in Models
local cache: { [string]: { number } } = {}

local function dataFor(id: string): { number }?
	local data = cache[id]
	if data then
		return data
	end
	local source = models:FindFirstChild(id)
	if not source or not source:IsA("ModuleScript") then
		return nil
	end
	data = require(source) :: { number }
	cache[id] = data
	return data
end

function ModelBuilder.has(id: string): boolean
	return dataFor(id) ~= nil
end

-- The middle of a model and the size of the box around it, in the model's own frame.
-- Turned parts are counted by their longest side, so the box is a little generous.
function ModelBuilder.bounds(id: string): (Vector3, Vector3)
	local data = dataFor(id)
	if not data or #data == 0 then
		return Vector3.zero, Vector3.one
	end
	local lo = Vector3.new(math.huge, math.huge, math.huge)
	local hi = -lo
	for i = 1, #data, STRIDE do
		local half = math.max(data[i + 1], data[i + 2], data[i + 3]) / 2
		local at = Vector3.new(data[i + 4], data[i + 5], data[i + 6])
		local reach = Vector3.new(half, half, half)
		lo = lo:Min(at - reach)
		hi = hi:Max(at + reach)
	end
	return (lo + hi) / 2, hi - lo
end

-- `base` is the centre of the model's footprint at the height of a cell's centre. `scale` shrinks
-- or grows the whole model about that point.
function ModelBuilder.build(parent: Instance, base: CFrame, id: string, scale: number?): Folder?
	local data = dataFor(id)
	if not data then
		return nil
	end
	local k = scale or 1
	local folder = Instance.new("Folder")
	folder.Name = "Visual"
	for i = 1, #data, STRIDE do
		local colour = Palette[data[i + 16] + 1]
		local part = Instance.new("Part")
		part.Shape = SHAPES[data[i]]
		part.Size = Vector3.new(data[i + 1], data[i + 2], data[i + 3]) * k
		part.CFrame = base
			* CFrame.new(
				data[i + 4] * k,
				data[i + 5] * k,
				data[i + 6] * k,
				data[i + 7],
				data[i + 8],
				data[i + 9],
				data[i + 10],
				data[i + 11],
				data[i + 12],
				data[i + 13],
				data[i + 14],
				data[i + 15]
			)
		part.Color = Color3.fromRGB(colour[1], colour[2], colour[3])
		part.Material = if colour[4] then Enum.Material.Neon else Enum.Material.SmoothPlastic
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
		part.Parent = folder
	end
	folder.Parent = parent
	return folder
end

return ModelBuilder
