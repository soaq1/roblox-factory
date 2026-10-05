-- Shows where electricity reaches. While a pole or a generator is in the hand (at the spot it
-- would be placed), or while the cursor rests on one that is already placed, a faint ball marks how
-- far it feeds machines and lines run to the poles and generators it joins up with.
--
-- The distances come from shared/PowerLogic, the same numbers the server's power system uses, so
-- what is shown is what will happen. Everything drawn here is only on this player's screen.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Defs = require(Shared:WaitForChild("Defs"))
local Grid = require(Shared:WaitForChild("Grid"))
local PowerLogic = require(Shared:WaitForChild("PowerLogic"))
local Screens = require(script.Parent.Screens)

local PowerOverlay = {}

local player = Players.LocalPlayer
local CELL = Config.CELL
local SETTINGS = PowerLogic.settings(CELL)
local LOOK_SECONDS = 0.1 -- how often the picture is worked out again
local REACH_COLOUR = Color3.fromRGB(240, 200, 70)
local LINK_COLOUR = Color3.fromRGB(255, 235, 150)
-- How the power system sees each kind of power machine.
local KIND = {
	pole = "pole",
	generator = "source",
	incinerator = "source",
	wind = "source",
	solar = "source",
	reactor = "source",
	battery = "battery",
}

type Spot = { x: number, y: number, z: number, kind: string, everywhere: boolean?, top: Vector3 }

local hotbar
local holder: Folder? = nil
local ball: Part
local lines: { Part } = {}
local shown = false

local function folder(): Folder
	if not holder or not holder.Parent then
		local made = Instance.new("Folder")
		made.Name = "PowerOverlay"
		made.Parent = Workspace.CurrentCamera
		holder = made
		lines = {}
		ball = Instance.new("Part")
		ball.Name = "Reach"
		ball.Shape = Enum.PartType.Ball
		ball.Anchored = true
		ball.CanCollide = false
		ball.CanQuery = false
		ball.CanTouch = false
		ball.CastShadow = false
		ball.Material = Enum.Material.ForceField
		ball.Color = REACH_COLOUR
		ball.Transparency = 0.55
		ball.Parent = made
	end
	return holder :: Folder
end

local function line(index: number): Part
	local part = lines[index]
	if not part then
		part = Instance.new("Part")
		part.Name = "Link"
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
		part.Material = Enum.Material.Neon
		part.Color = LINK_COLOUR
		part.Parent = folder()
		lines[index] = part
	end
	return part
end

local function hide()
	if not shown then
		return
	end
	shown = false
	if holder then
		ball.Transparency = 1
		for _, part in lines do
			part.Transparency = 1
		end
	end
end

-- Where a power machine's wires would be tied: just under its top.
local function topOf(centre: Vector3, def): Vector3
	return centre + Vector3.new(0, -CELL / 2 + def.height - 0.5, 0)
end

-- A placed machine as the power system sees it. The centre is read from the machine's body, which
-- is centred on its footprint and stands on the floor of its cell.
local function spotOf(model: Instance): Spot?
	local def = Defs.Machines[model:GetAttribute("Machine") :: any]
	local kind = def and def.behavior == "power" and KIND[def.power]
	local body = model:FindFirstChild("Body")
	if not def or not kind or not body or not body:IsA("BasePart") then
		return nil
	end
	local height = math.max(def.height, 1)
	local centre = body.Position + Vector3.new(0, CELL / 2 - height / 2, 0)
	return {
		x = centre.X,
		y = centre.Y,
		z = centre.Z,
		kind = kind,
		everywhere = def.power == "reactor",
		top = topOf(centre, def),
	}
end

-- What the cursor is on: the hit, or nil. Parts that take no part in queries (the build outline,
-- the held item) are passed through, as are the character and loose items.
local function cursorHit(): RaycastResult?
	local camera = Workspace.CurrentCamera
	if not camera then
		return nil
	end
	local ignore: { Instance } = {}
	if player.Character then
		table.insert(ignore, player.Character)
	end
	local items = Workspace:FindFirstChild("Items")
	if items then
		table.insert(ignore, items)
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local mouse = UserInputService:GetMouseLocation()
	local ray = camera:ViewportPointToRay(mouse.X, mouse.Y)
	return Workspace:Raycast(ray.Origin, ray.Direction * 400, params)
end

-- The island folder something stands on, if any.
local function islandOf(instance: Instance): Instance?
	local at: Instance? = instance
	while at and at.Parent ~= Workspace do
		at = at.Parent
	end
	return if at and string.sub(at.Name, 1, 7) == "Island_" then at else nil
end

-- What to draw the reach of, and the island whose other power machines it may join:
-- a power machine in the hand, at the cell it would be placed in, or one under the cursor.
local function focus(): (Spot?, Instance?, Instance?)
	local hit = cursorHit()
	if not hit then
		return nil, nil, nil
	end
	local held = Defs.Machines[hotbar.selected()]
	local heldKind = held and held.behavior == "power" and KIND[held.power]
	if held and heldKind then
		local origin = player:GetAttribute("IslandOrigin")
		local island = Workspace:FindFirstChild("Island_" .. player.UserId)
		if typeof(origin) ~= "Vector3" or not island or not hit.Instance:IsDescendantOf(island) then
			return nil, nil, nil
		end
		-- the empty cell just outside the surface the cursor is on
		local outside = hit.Position + hit.Normal * 0.1
		local centre = origin
			+ Vector3.new(
				Grid.toCell(outside.X, origin.X, CELL) * CELL,
				Grid.toCell(outside.Y, origin.Y, CELL) * CELL,
				Grid.toCell(outside.Z, origin.Z, CELL) * CELL
			)
		return {
			x = centre.X,
			y = centre.Y,
			z = centre.Z,
			kind = heldKind,
			everywhere = held.power == "reactor",
			top = topOf(centre, held),
		},
			island,
			nil
	end
	local model = hit.Instance:FindFirstAncestorOfClass("Model")
	local spot = model and spotOf(model)
	if model and spot then
		return spot, islandOf(model), model
	end
	return nil, nil, nil
end

local function look()
	if Screens.anyOpen() then
		hide()
		return
	end
	local spot, island, self = focus()
	if not spot or not island then
		hide()
		return
	end
	local machines = island:FindFirstChild("Machines")
	local others: { Spot } = {}
	if machines then
		for _, model in machines:GetChildren() do
			if model ~= self then
				local other = spotOf(model)
				if other then
					table.insert(others, other)
				end
			end
		end
	end
	local reach, joined = PowerLogic.preview(spot :: any, others :: any, SETTINGS)
	folder()
	shown = true
	if reach > 0 then
		ball.Size = Vector3.new(reach * 2, reach * 2, reach * 2)
		ball.Position = Vector3.new(spot.x, spot.y, spot.z)
		ball.Transparency = 0.55
	else
		ball.Transparency = 1
	end
	for index, which in joined do
		local to = others[which].top
		local length = (to - spot.top).Magnitude
		local part = line(index)
		if length > 0.05 then
			part.Size = Vector3.new(0.18, 0.18, length)
			part.CFrame = CFrame.lookAt((spot.top + to) / 2, to)
			part.Transparency = 0.2
		else
			part.Transparency = 1
		end
	end
	for index = #joined + 1, #lines do
		lines[index].Transparency = 1
	end
end

function PowerOverlay.init(hotbarUi)
	hotbar = hotbarUi
	local since = 0
	RunService.RenderStepped:Connect(function(dt)
		since += dt
		if since >= LOOK_SECONDS then
			since = 0
			look()
		end
	end)
end

return PowerOverlay
