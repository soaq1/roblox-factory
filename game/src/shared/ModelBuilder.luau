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

-- `base` is the centre of the model's footprint at the height of a cell's centre.
function ModelBuilder.build(parent: Instance, base: CFrame, id: string): Folder?
	local data = dataFor(id)
	if not data then
		return nil
	end
	local folder = Instance.new("Folder")
	folder.Name = "Visual"
	for i = 1, #data, STRIDE do
		local colour = Palette[data[i + 16] + 1]
		local part = Instance.new("Part")
		part.Shape = SHAPES[data[i]]
		part.Size = Vector3.new(data[i + 1], data[i + 2], data[i + 3])
		part.CFrame = base
			* CFrame.new(
				data[i + 4],
				data[i + 5],
				data[i + 6],
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
