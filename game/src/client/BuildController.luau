-- Turns mouse and keyboard input into place, break, drop and pick-up requests, and draws the
-- outline showing where the next thing will go. Left click uses whatever is in the hand: a block or
-- machine is placed, a tool breaks, anything else does nothing. Q lets go of the item in the hand,
-- R turns a machine before it is placed, F picks up, Shift runs. Right click is left to the camera.
-- The server decides whether each request is allowed.
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
local ToolLogic = require(Shared:WaitForChild("ToolLogic"))
local HandView = require(script.Parent.HandView)
local Screens = require(script.Parent.Screens)

local BuildController = {}

local player = Players.LocalPlayer
local CELL = Config.CELL
local FREE = Color3.fromRGB(120, 220, 140)
local BLOCKED = Color3.fromRGB(230, 90, 80)
local MARK = Color3.fromRGB(255, 255, 255)
local WALK_SPEED = 16
local RUN_SPEED = 26 -- while Shift is held
local DROP_SECONDS = 0.15 -- between items while Q is held

local hotbar
local dir = 0
local ghost: Part
local arrow: Part
local SWING_SECONDS = 0.2 -- how often a held left button swings again
-- The cell being broken while the left button is held. Holding only ever works on the cell the
-- press began on, so sweeping the cursor never tears through a row of machines.
local breaking: Target? = nil
local sinceSwing = 0
local dropping = false
local sinceDrop = 0

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
	[Enum.KeyCode.Zero] = 10,
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
	-- The pad the player arrives on is not a block and cannot be built against.
	local island = Workspace:FindFirstChild("Island_" .. player.UserId)
	local pad = island and island:FindFirstChild("SpawnPad")
	if pad then
		table.insert(list, pad)
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
		-- A machine's shape does not fill its cells exactly, so the hit height is fitted to the
		-- layers the machine keeps. Any of its cells stands for the whole machine.
		local base = model:GetAttribute("CellY") :: number
		if sy > 0 then
			hy = base + def.sy - 1
		elseif sy < 0 then
			hy = base
		else
			hy = math.clamp(hy, base, base + def.sy - 1)
		end
		by = hy
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

-- What left click would do with the thing in the hand: "place", "break", or nil. Only blocks,
-- machines and tools do anything; any other item is just carried.
local function intent(): string?
	local entry = hotbar.selected()
	local item = Defs.itemOf(entry)
	if item then
		return if ToolLogic.parse(item) then "break" else nil
	end
	return if Defs.isPlaceable(entry) then "place" else nil
end

-- Q: lets go of one of the items in the hand. It lands on the cell the cursor points at, or
-- failing that in front of the player. Blocks and machines are not loose things and stay put.
local function dropHeld()
	local item = Defs.itemOf(hotbar.selected())
	if not item or Screens.anyOpen() then
		return
	end
	HandView.swing()
	local found = target()
	if found then
		Net.get("Drop"):FireServer(item, found.px, found.py, found.pz)
	else
		Net.get("Drop"):FireServer(item)
	end
end

local function setRunning(running: boolean)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.WalkSpeed = if running then RUN_SPEED else WALK_SPEED
	end
end

local function drawGhost()
	local at = origin()
	local found = if Screens.anyOpen() then nil else target()
	local what = intent()
	if not at or not found or not what then
		ghost.Transparency = 1
		arrow.Transparency = 1
		return
	end
	arrow.Transparency = 1
	if what == "break" then
		-- With a tool in the hand, mark the thing that would be broken.
		ghost.Size = Vector3.new(CELL, CELL, CELL) * 1.02
		ghost.CFrame = CFrame.new(cellCenter(at, found.bx, found.by, found.bz))
		ghost.Color = MARK
		ghost.Transparency = 0.8
		return
	end
	local center = cellCenter(at, found.px, found.py, found.pz)
	local def = Defs.Machines[hotbar.selected()]
	local box, size = CFrame.new(center), Vector3.new(CELL, CELL, CELL)
	if def and what == "place" then
		-- A machine's outline covers every cell it will take. The aimed cell is its back-left corner.
		local cx, cz = Grid.footprintCentre(dir, def.sx, def.sz)
		box = CFrame.new(center + Vector3.new(cx * CELL, (def.sy - 1) * CELL / 2, cz * CELL))
			* CFrame.Angles(0, -dir * math.pi / 2, 0)
		size = Vector3.new(def.sx * CELL, def.sy * CELL, def.sz * CELL)
		-- The arrow points the way things will come out.
		arrow.CFrame = box * CFrame.new(size.X / 2 - 0.8, size.Y / 2 + 0.1, 0)
		arrow.Transparency = 0
	end
	ghost.Size = size * 0.98
	ghost.CFrame = box
	ghost.Color = if isOccupied(box, size) then BLOCKED else FREE
	ghost.Transparency = 0.6
end

-- Uses what is in the hand on whatever the cursor points at. Returns the cell being broken when
-- that is what happened, so the swing can be kept up while the button is held.
local function use(): Target?
	local found = if Screens.anyOpen() then nil else target()
	local what = intent()
	if not found or not what then
		return nil
	end
	HandView.swing()
	if what == "break" then
		Net.get("Break"):FireServer(found.bx, found.by, found.bz)
		return found
	end
	Net.get("Place"):FireServer(hotbar.selected(), found.px, found.py, found.pz, dir)
	return nil
end

local function onInputBegan(input: InputObject, handledByUi: boolean)
	if handledByUi then
		return
	end
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		breaking = use()
		sinceSwing = 0
	elseif input.KeyCode == Enum.KeyCode.R then
		dir = Grid.rotate(dir, 1)
	elseif input.KeyCode == Enum.KeyCode.Q then
		dropHeld()
		dropping = true
		sinceDrop = 0
	elseif input.KeyCode == Enum.KeyCode.LeftShift then
		setRunning(true)
	elseif input.KeyCode == Enum.KeyCode.F then
		Net.get("Pickup"):FireServer()
	elseif keys[input.KeyCode] then
		hotbar.select(keys[input.KeyCode])
	end
end

-- While the left button stays down on the same cell with a tool in the hand, swing at it again
-- every so often. In survival mode a block takes several swings; once it is gone the cursor finds
-- another cell and the swinging stops.
local function keepBreaking(dt: number)
	local first = breaking
	if not first then
		return
	end
	sinceSwing += dt
	if sinceSwing < SWING_SECONDS then
		return
	end
	sinceSwing = 0
	local found = if Screens.anyOpen() then nil else target()
	if
		intent() ~= "break"
		or not found
		or found.bx ~= first.bx
		or found.by ~= first.by
		or found.bz ~= first.bz
	then
		breaking = nil
		return
	end
	HandView.swing()
	Net.get("Break"):FireServer(found.bx, found.by, found.bz)
end

-- Holding Q keeps letting go of items, one at a time.
local function keepDropping(dt: number)
	if not dropping then
		return
	end
	sinceDrop += dt
	if sinceDrop >= DROP_SECONDS then
		sinceDrop = 0
		dropHeld()
	end
end

local function onInputEnded(input: InputObject)
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		breaking = nil
	elseif input.KeyCode == Enum.KeyCode.Q then
		dropping = false
	elseif input.KeyCode == Enum.KeyCode.LeftShift then
		setRunning(false)
	end
end

function BuildController.init(hotbarUi)
	hotbar = hotbarUi
	makeGhost()
	UserInputService.InputBegan:Connect(onInputBegan)
	UserInputService.InputEnded:Connect(onInputEnded)
	RunService.RenderStepped:Connect(drawGhost)
	RunService.RenderStepped:Connect(keepBreaking)
	RunService.RenderStepped:Connect(keepDropping)
end

return BuildController
