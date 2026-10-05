-- Turns mouse and keyboard input into place, break and pick-up requests, and draws the outline
-- showing where the next thing will go. The server decides whether each request is allowed.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Defs = require(Shared:WaitForChild("Defs"))
local Grid = require(Shared:WaitForChild("Grid"))
local Net = require(Shared:WaitForChild("Net"))

local BuildController = {}

local player = Players.LocalPlayer
local CELL = Config.CELL
local CLICK_SECONDS = 0.35 -- a right press longer than this, or that moves, is a camera drag
local CLICK_PIXELS = 8
local FREE = Color3.fromRGB(120, 220, 140)
local BLOCKED = Color3.fromRGB(230, 90, 80)

local hotbar
local dir = 0
local ghost: Part
local arrow: Part
local rightDownAt: number? = nil
local rightDragged = 0 -- pixels the mouse travelled while the right button was held

local keys = {
	[Enum.KeyCode.One] = 1,
	[Enum.KeyCode.Two] = 2,
	[Enum.KeyCode.Three] = 3,
	[Enum.KeyCode.Four] = 4,
	[Enum.KeyCode.Five] = 5,
	[Enum.KeyCode.Six] = 6,
	[Enum.KeyCode.Seven] = 7,
	[Enum.KeyCode.Eight] = 8,
	[Enum.KeyCode.Nine] = 9,
}

local function origin(): Vector3?
	local value = player:GetAttribute("IslandOrigin")
	return if typeof(value) == "Vector3" then value else nil
end

local function cellCenter(at: Vector3, x: number, y: number, z: number): Vector3
	return at + Vector3.new(x * CELL, y * CELL, z * CELL)
end

local function ignoreList(): { Instance }
	local list: { Instance } = { ghost, arrow }
	if player.Character then
		table.insert(list, player.Character)
	end
	local items = Workspace:FindFirstChild("Items")
	if items then
		table.insert(list, items)
	end
	return list
end

-- Snaps a surface normal to the nearest axis, as whole-number steps.
local function axisStep(normal: Vector3): (number, number, number)
	local ax, ay, az = math.abs(normal.X), math.abs(normal.Y), math.abs(normal.Z)
	if ay >= ax and ay >= az then
		return 0, math.sign(normal.Y), 0
	elseif ax >= az then
		return math.sign(normal.X), 0, 0
	end
	return 0, 0, math.sign(normal.Z)
end

export type Target = { bx: number, by: number, bz: number, px: number, py: number, pz: number }

-- What the cursor points at on my island: the cell that would be broken (b) and the empty
-- neighbour a new thing would go into (p).
local function target(): Target?
	local at = origin()
	local camera = Workspace.CurrentCamera
	local island = Workspace:FindFirstChild("Island_" .. player.UserId)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not at or not camera or not island or not root or not root:IsA("BasePart") then
		return nil
	end
	local mouse = UserInputService:GetMouseLocation()
	local ray = camera:ViewportPointToRay(mouse.X, mouse.Y)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignoreList()
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 400, params)
	if not hit or not hit.Instance:IsDescendantOf(island) then
		return nil
	end

	-- The cell that was hit, and the step from it to the neighbour a new thing would go into.
	local inside = hit.Position - hit.Normal * 0.1
	local hx = Grid.toCell(inside.X, at.X, CELL)
	local hy = Grid.toCell(inside.Y, at.Y, CELL)
	local hz = Grid.toCell(inside.Z, at.Z, CELL)
	local sx, sy, sz = axisStep(hit.Normal)
	local bx, by, bz = hx, hy, hz
	local model = hit.Instance:FindFirstAncestorOfClass("Model")
	local def = model and Defs.Machines[model:GetAttribute("Machine") :: any]
	if model and def then
		-- A machine is broken by its anchor cell, whichever part of it was hit. Its shape does not
		-- fill its cells exactly, so the hit height is fitted to the layers the machine keeps.
		bx = model:GetAttribute("CellX") :: number
		by = model:GetAttribute("CellY") :: number
		bz = model:GetAttribute("CellZ") :: number
		if sy > 0 then
			hy = by + def.sy - 1
		elseif sy < 0 then
			hy = by
		else
			hy = math.clamp(hy, by, by + def.sy - 1)
		end
	end
	local found: Target = { bx = bx, by = by, bz = bz, px = hx + sx, py = hy + sy, pz = hz + sz }
	if (cellCenter(at, found.px, found.py, found.pz) - root.Position).Magnitude > Config.REACH then
		return nil
	end
	return found
end

local function isOccupied(box: CFrame, size: Vector3): boolean
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignoreList()
	return #Workspace:GetPartBoundsInBox(box, size - Vector3.new(0.4, 0.4, 0.4), params) > 0
end

local function makeGhost()
	ghost = Instance.new("Part")
	ghost.Name = "BuildGhost"
	ghost.Anchored = true
	ghost.CanCollide = false
	ghost.CanQuery = false
	ghost.CanTouch = false
	ghost.Size = Vector3.new(CELL, CELL, CELL) * 0.98
	ghost.Material = Enum.Material.SmoothPlastic
	ghost.Transparency = 1
	ghost.Parent = Workspace

	arrow = Instance.new("Part")
	arrow.Name = "BuildArrow"
	arrow.Anchored = true
	arrow.CanCollide = false
	arrow.CanQuery = false
	arrow.CanTouch = false
	arrow.Size = Vector3.new(1.6, 0.2, 0.5)
	arrow.Material = Enum.Material.Neon
	arrow.Color = Color3.new(1, 1, 1)
	arrow.Transparency = 1
	arrow.Parent = Workspace
end

local function drawGhost()
	local at = origin()
	local found = if hotbar.isPaletteOpen() then nil else target()
	if not at or not found then
		ghost.Transparency = 1
		arrow.Transparency = 1
		return
	end
	local center = cellCenter(at, found.px, found.py, found.pz)
	local def = Defs.Machines[hotbar.selected()]
	local box, size = CFrame.new(center), Vector3.new(CELL, CELL, CELL)
	if def then
		-- A machine's outline covers every cell it will take. The aimed cell is its back-left corner.
		local cx, cz = Grid.footprintCentre(dir, def.sx, def.sz)
		box = CFrame.new(center + Vector3.new(cx * CELL, (def.sy - 1) * CELL / 2, cz * CELL))
			* CFrame.Angles(0, -dir * math.pi / 2, 0)
		size = Vector3.new(def.sx * CELL, def.sy * CELL, def.sz * CELL)
	end
	ghost.Size = size * 0.98
	ghost.CFrame = box
	ghost.Color = if isOccupied(box, size) then BLOCKED else FREE
	ghost.Transparency = 0.6
	if def then
		-- The arrow points the way things will come out.
		arrow.CFrame = box * CFrame.new(size.X / 2 - 0.8, size.Y / 2 + 0.1, 0)
		arrow.Transparency = 0
	else
		arrow.Transparency = 1
	end
end

local function onInputBegan(input: InputObject, handledByUi: boolean)
	if handledByUi then
		return
	end
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		local found = if hotbar.isPaletteOpen() then nil else target()
		if found then
			Net.get("Break"):FireServer(found.bx, found.by, found.bz)
		end
	elseif input.UserInputType == Enum.UserInputType.MouseButton2 then
		rightDownAt = os.clock()
		rightDragged = 0
	elseif input.KeyCode == Enum.KeyCode.R then
		dir = Grid.rotate(dir, 1)
	elseif input.KeyCode == Enum.KeyCode.E then
		hotbar.togglePalette()
	elseif input.KeyCode == Enum.KeyCode.F then
		Net.get("Pickup"):FireServer()
	elseif keys[input.KeyCode] then
		hotbar.select(keys[input.KeyCode])
	end
end

local function onInputEnded(input: InputObject)
	if input.UserInputType ~= Enum.UserInputType.MouseButton2 or not rightDownAt then
		return
	end
	local held = os.clock() - rightDownAt
	rightDownAt = nil
	if held > CLICK_SECONDS or rightDragged > CLICK_PIXELS or hotbar.isPaletteOpen() then
		return
	end
	local found = target()
	if not found then
		return
	end
	local entry = hotbar.selected()
	local item = Defs.itemOf(entry)
	if item then
		Net.get("Drop"):FireServer(item, found.px, found.py, found.pz)
	else
		Net.get("Place"):FireServer(entry, found.px, found.py, found.pz, dir)
	end
end

-- While the right button is held Roblox pins the cursor to turn the camera, so the cursor position
-- does not change. The movement has to be added up from the raw deltas instead.
local function onInputChanged(input: InputObject)
	if rightDownAt and input.UserInputType == Enum.UserInputType.MouseMovement then
		rightDragged += Vector2.new(input.Delta.X, input.Delta.Y).Magnitude
	end
end

function BuildController.init(hotbarUi)
	hotbar = hotbarUi
	makeGhost()
	UserInputService.InputBegan:Connect(onInputBegan)
	UserInputService.InputEnded:Connect(onInputEnded)
	UserInputService.InputChanged:Connect(onInputChanged)
	RunService.RenderStepped:Connect(drawGhost)
end

return BuildController
