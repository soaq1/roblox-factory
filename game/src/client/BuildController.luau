-- Turns what the player does with their hand into place, break, drop and pick-up requests, and
-- draws the outline showing where the next thing will go. Using the hand (left click, a tap, the
-- right trigger) does whatever fits the thing held: a block or machine is placed, a tool breaks,
-- anything else does nothing. Q lets go of the item in the hand, R turns a machine before it is
-- placed, F picks up, Shift runs, the middle button takes the thing looked at into the hand.
-- Right click is left to the camera. The server decides whether each request is allowed.
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Defs = require(Shared:WaitForChild("Defs"))
local Grid = require(Shared:WaitForChild("Grid"))
local HandLogic = require(Shared:WaitForChild("HandLogic"))
local ModelBuilder = require(Shared:WaitForChild("ModelBuilder"))
local Net = require(Shared:WaitForChild("Net"))
local Stock = require(Shared:WaitForChild("Stock"))(Defs)
local ToolLogic = require(Shared:WaitForChild("ToolLogic"))
local HandInput = require(script.Parent.HandInput)
local HandView = require(script.Parent.HandView)
local Screens = require(script.Parent.Screens)
local Settings = require(script.Parent.Settings)
local SoundPlayer = require(script.Parent.SoundPlayer)
local UIKit = require(script.Parent.UIKit)

local BuildController = {}

local player = Players.LocalPlayer
local CELL = Config.CELL
local FREE = Color3.fromRGB(120, 220, 140)
local BLOCKED = Color3.fromRGB(230, 90, 80)
local MARK = Color3.fromRGB(255, 255, 255)
local MOUTH_IN = Color3.fromRGB(240, 180, 41) -- the yellow of an input mouth
local MOUTH_OUT = Color3.fromRGB(53, 184, 166) -- the teal of an output mouth
local WALK_SPEED = 16
local RUN_SPEED = 26 -- while running
local DROP_SECONDS = 0.15 -- between items while Q is held
local PICKUP_SECONDS = 0.125 -- between pick-ups while F is held: about eight a second
local SWING_SECONDS = 0.2 -- how often a held use swings again
local LAY_SECONDS = 0.05 -- the least time between two things laid in one drag
local GATE_SECONDS = 0.15 -- how often the prompts near the player are looked over
local PROMPT_SIGHT = 26 -- studs: machines nearer than this have their prompts looked over
local TOUCH_PROMPT_RANGE = 8 -- studs: on touch, the nearest machine within this is "aimed at"

local hotbar
local dir = 0
local ghost: Part
local arrow: Part
-- The thing being broken while use is held. A hold stays on the cell the press began on; when
-- that is a block and it breaks, the hold carries on to the next block under the cursor. It never
-- carries on to a machine, or on from one, so sweeping the cursor cannot tear through a factory.
local breaking: Target? = nil
local sinceSwing = 0
-- What has been laid during the present hold, when a block or machine is being dragged out.
local laying: { last: { number }, placed: { [string]: boolean } }? = nil
local sinceLay = 0
local dropping = false
local sinceDrop = 0
local picking = false
local sincePick = 0
local running = false
local promptsShown = 0
local lastHint = 0
local sinceGate = 0

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

export type Target = {
	bx: number,
	by: number,
	bz: number,
	px: number,
	py: number,
	pz: number,
	part: BasePart, -- what the pointing line struck
	model: Model?, -- the machine it belongs to, if it is one
}

local function character(): (Model?, BasePart?)
	local body = player.Character
	local root = body and body:FindFirstChild("HumanoidRootPart")
	if body and root and root:IsA("BasePart") then
		return body, root
	end
	return nil, nil
end

-- What the player points at on their own island: the cell that would be broken (b) and the empty
-- neighbour a new thing would go into (p).
local function target(): Target?
	local at = origin()
	local ray = HandInput.ray()
	local island = Workspace:FindFirstChild("Island_" .. player.UserId)
	local _, root = character()
	if not at or not ray or not island or not root then
		return nil
	end
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
		if def.behavior == "tree" then
			-- A trunk leans through cells of its own choosing; the cell it stands in is the sure one.
			bx = model:GetAttribute("CellX") :: number
			by = base
			bz = model:GetAttribute("CellZ") :: number
		end
	end
	local found: Target = {
		bx = bx,
		by = by,
		bz = bz,
		px = hx + sx,
		py = hy + sy,
		pz = hz + sz,
		part = hit.Instance,
		model = if def then model else nil,
	}
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

-- The see-through copy of the machine in the hand, drawn where it would be placed, with its
-- mouths marked: yellow where things go in, teal where they come out.
type Piece = { part: BasePart, offset: CFrame }
local outline: { entry: string, folder: Folder, pieces: { Piece }, mouths: number, shown: boolean }? = nil

local SIDES = {
	E = Vector3.new(1, 0, 0),
	W = Vector3.new(-1, 0, 0),
	S = Vector3.new(0, 0, 1),
	N = Vector3.new(0, 0, -1),
}

local function clearOutline()
	if outline then
		outline.folder:Destroy()
		outline = nil
	end
end

-- Builds the outline for a machine entry. Everything is built around the machine's own frame
-- (the centre of its footprint at cell-centre height) and moved as one each frame.
local function buildOutline(entry: string, def)
	clearOutline()
	local folder = Instance.new("Folder")
	folder.Name = "BuildOutline"
	local pieces: { Piece } = {}

	-- The model itself, where this exact machine has one. A left corner or an open belt borrows
	-- another's picture, which would show the wrong shape, so those get mouths and a box only.
	local id: string? = if def.stages then def.stages[1] elseif ModelBuilder.has(entry) then entry else nil
	if id then
		local built = ModelBuilder.build(folder, CFrame.new(), id)
		if built then
			for _, part in built:GetChildren() do
				if part:IsA("BasePart") then
					part.Transparency = 0.5
					table.insert(pieces, { part = part, offset = part.CFrame })
				end
			end
		end
	end

	local ports = def.ports
	if #ports == 0 and def.behavior == "belt" then
		ports = HandLogic.beltPorts(def.shape)
	end
	for _, port in ports do
		local outward = SIDES[port.side]
		if outward then
			local alongX = port.side == "E" or port.side == "W"
			local half = (if alongX then def.sx else def.sz) * CELL / 2
			local lateral = if alongX
				then Vector3.new(0, 0, -port.off * CELL)
				else Vector3.new(port.off * CELL, 0, 0)
			local mouth = Instance.new("Part")
			mouth.Name = "Mouth"
			mouth.Anchored = true
			mouth.CanCollide = false
			mouth.CanQuery = false
			mouth.CanTouch = false
			mouth.CastShadow = false
			mouth.Material = Enum.Material.Neon
			mouth.Color = if port.kind == "in" then MOUTH_IN else MOUTH_OUT
			mouth.Transparency = 0.25
			mouth.Size = if alongX then Vector3.new(0.2, 1.5, 2) else Vector3.new(2, 1.5, 0.2)
			mouth.Parent = folder
			local offset = CFrame.new(outward * (half + 0.35) + lateral + Vector3.new(0, -0.55, 0))
			table.insert(pieces, { part = mouth, offset = offset })
		end
	end
	outline = { entry = entry, folder = folder, pieces = pieces, mouths = #ports, shown = false }
end

local function showOutline(base: CFrame)
	local current = outline
	if not current then
		return
	end
	for _, piece in current.pieces do
		piece.part.CFrame = base * piece.offset
	end
	if not current.shown then
		current.shown = true
		current.folder.Parent = Workspace
	end
end

local function hideOutline()
	if outline and outline.shown then
		outline.shown = false
		outline.folder.Parent = nil
	end
end

-- What using the hand would do with the thing in it: "place", "break", or nil. Only blocks,
-- machines and tools do anything; any other item is just carried.
local function intent(): string?
	local entry = hotbar.selected()
	local item = Defs.itemOf(entry)
	if item then
		return if ToolLogic.parse(item) then "break" else nil
	end
	return if Defs.isPlaceable(entry) then "place" else nil
end

local function isCreative(): boolean
	return hotbar.state.mode == "creative"
end

-- Q: lets go of one of the things in the hand. It lands on the cell the player points at, or
-- failing that in front of them. A block that is also an item (a log, stone, ore) goes as that
-- item, so one slot serves for building with it and for feeding it to a machine. Machines and
-- blocks that are only blocks are not loose things and stay put.
local function dropHeld()
	local entry = hotbar.selected()
	if entry == "" or Screens.anyOpen() then
		return
	end
	local item = HandLogic.looseForm(Defs, Stock, entry, hotbar.bag, isCreative())
	if not item then
		dropping = false
		if os.clock() - lastHint > 2 then
			lastHint = os.clock()
			UIKit.toast(Defs.name(entry) .. "은(는) 바닥에 내려놓을 수 없습니다")
		end
		return
	end
	HandView.swing()
	SoundPlayer.play("drop")
	local found = target()
	if found then
		Net.get("Drop"):FireServer(item, found.px, found.py, found.pz)
	else
		Net.get("Drop"):FireServer(item)
	end
end

-- The loose item the player points at, if any. Walls are looked through: only items count.
local function aimedItem(): Instance?
	local items = Workspace:FindFirstChild("Items")
	local ray = HandInput.ray()
	if not items or not ray or HandInput.mode() == "touch" then
		return nil
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { items }
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 200, params)
	return if hit then hit.Instance else nil
end

-- F: picks up one stack. F also answers whatever prompt is on screen (a portal, a workbench, a
-- ripe crop); then it is not a pick-up as well.
-- `repeated` is a pick-up made by holding the key down rather than pressing it.
local function pickUp(repeated: boolean?)
	if promptsShown > 0 or Screens.anyOpen() then
		return
	end
	SoundPlayer.play("pickup")
	Net.get("Pickup"):FireServer(aimedItem(), repeated == true)
end

local function setRunning(now: boolean)
	running = now
	local body = player.Character
	local humanoid = body and body:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.WalkSpeed = if now then RUN_SPEED else WALK_SPEED
	end
end

local function drawGhost()
	local at = origin()
	local found = if Screens.anyOpen() then nil else target()
	local what = intent()
	if not at or not found or not what then
		ghost.Transparency = 1
		arrow.Transparency = 1
		hideOutline()
		return
	end
	arrow.Transparency = 1
	if what == "break" then
		-- With a tool in the hand, mark the thing that would be broken.
		hideOutline()
		ghost.Size = Vector3.new(CELL, CELL, CELL) * 1.02
		ghost.CFrame = CFrame.new(cellCenter(at, found.bx, found.by, found.bz))
		ghost.Color = MARK
		ghost.Transparency = 0.8
		return
	end
	local entry = hotbar.selected()
	local center = cellCenter(at, found.px, found.py, found.pz)
	local def = Defs.Machines[entry]
	if not def then
		-- A block: a plain box in the cell it would fill.
		hideOutline()
		local box = CFrame.new(center)
		local size = Vector3.new(CELL, CELL, CELL)
		ghost.Size = size * 0.98
		ghost.CFrame = box
		-- The player's own body is left out of isOccupied, so it is asked about here: the server
		-- places nothing in a cell someone stands in.
		local _, root = character()
		local inBody = root ~= nil
			and HandLogic.bodyInCell(
				center.X,
				center.Y,
				center.Z,
				CELL,
				root.Position.X,
				root.Position.Y,
				root.Position.Z
			)
		ghost.Color = if inBody or isOccupied(box, size) then BLOCKED else FREE
		ghost.Transparency = 0.6
		return
	end
	-- A machine: its own shape where it would stand, over a faint box covering every cell it will
	-- take. The aimed cell is its back-left corner.
	if not outline or outline.entry ~= entry then
		buildOutline(entry, def)
	end
	local cx, cz = Grid.footprintCentre(dir, def.sx, def.sz)
	local base = CFrame.new(center + Vector3.new(cx * CELL, 0, cz * CELL))
		* CFrame.Angles(0, -dir * math.pi / 2, 0)
	local size = Vector3.new(def.sx * CELL, def.sy * CELL, def.sz * CELL)
	local box = base * CFrame.new(0, (def.sy - 1) * CELL / 2, 0)
	showOutline(base)
	ghost.Size = size * 0.98
	ghost.CFrame = box
	ghost.Color = if isOccupied(box, size) then BLOCKED else FREE
	ghost.Transparency = 0.85
	if outline and outline.mouths == 0 then
		-- Nothing goes in or out, so an arrow shows which way it faces.
		arrow.CFrame = box * CFrame.new(size.X / 2 - 0.8, size.Y / 2 + 0.1, 0)
		arrow.Transparency = 0
	end
end

-- Asks for the thing in the hand to be placed at a target, and notes every cell it would take.
local function placeAt(found: Target, placed: { [string]: boolean }?)
	local entry = hotbar.selected()
	HandView.swing()
	SoundPlayer.play("place")
	Net.get("Place"):FireServer(entry, found.px, found.py, found.pz, dir)
	if placed then
		local def = Defs.Machines[entry]
		if def then
			for _, key in HandLogic.covered(Grid, def, found.px, found.py, found.pz, dir) do
				placed[key] = true
			end
		else
			placed[Grid.key(found.px, found.py, found.pz)] = true
		end
	end
end

-- Uses what is in the hand on whatever the player points at.
local function use()
	breaking = nil
	laying = nil
	local found = if Screens.anyOpen() then nil else target()
	local what = intent()
	if found and not what and os.clock() - lastHint > 3 then
		-- Pointing at something with nothing usable in the hand: say what is missing.
		lastHint = os.clock()
		UIKit.toast(
			"부수려면 곡괭이나 도끼 같은 도구를, 놓으려면 블록이나 기계를 손에 드세요"
		)
	end
	if not found or not what then
		return
	end
	if what == "break" then
		HandView.swing()
		SoundPlayer.hit(nil)
		Net.get("Break"):FireServer(found.bx, found.by, found.bz)
		-- Holding keeps swinging at this same cell, if the player has that switched on.
		if Settings.get("holdToRepeat") then
			breaking = found
			sinceSwing = 0
		end
		return
	end
	local placed: { [string]: boolean } = {}
	placeAt(found, placed)
	-- Holding keeps laying into new cells, if the player has that switched on.
	if Settings.get("dragPlace") then
		laying = { last = { found.px, found.py, found.pz }, placed = placed }
		sinceLay = 0
	end
end

-- While use stays down with a tool in the hand, swing again every so often. In survival mode a
-- block takes several swings. When the block being worked is gone the swinging carries on to
-- whatever block is under the cursor next, so a tree or a trench is one long press. Lifting a
-- machine always takes a press of its own.
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
	if intent() ~= "break" or Screens.anyOpen() then
		breaking = nil
		return
	end
	local found = target()
	if not found then
		-- Nothing under the cursor just now. If the block has broken, wait for the next one to
		-- come under it; otherwise the cursor has left and the hold is over.
		if first.model or first.part.Parent then
			breaking = nil
		end
		return
	end
	if found.bx ~= first.bx or found.by ~= first.by or found.bz ~= first.bz then
		local firstGone = first.model == nil and first.part.Parent == nil
		if not firstGone or found.model then
			breaking = nil
			return
		end
		breaking = found
	end
	HandView.swing()
	SoundPlayer.hit(nil)
	Net.get("Break"):FireServer(found.bx, found.by, found.bz)
end

-- While use stays down with a block or machine in the hand, lay another into each new free cell
-- the player points at. Nothing is ever built against something laid during the same hold, so
-- dragging along the ground lays a row and never climbs into a tower. A straight belt turns to
-- face the way the drag is going.
local function keepLaying(dt: number)
	local run = laying
	if not run then
		return
	end
	sinceLay += dt
	if sinceLay < LAY_SECONDS then
		return
	end
	if intent() ~= "place" or Screens.anyOpen() then
		laying = nil
		return
	end
	local found = target()
	if not found then
		return
	end
	local into = Grid.key(found.px, found.py, found.pz)
	if run.placed[into] or run.placed[Grid.key(found.bx, found.by, found.bz)] then
		return
	end
	local def = Defs.Machines[hotbar.selected()]
	if def and def.behavior == "belt" and def.shape == "straight" then
		local facing =
			HandLogic.dragDir(found.px - run.last[1], found.py - run.last[2], found.pz - run.last[3])
		if facing then
			dir = facing
		end
	end
	sinceLay = 0
	placeAt(found, run.placed)
	run.last = { found.px, found.py, found.pz }
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

-- Holding F keeps picking up.
local function keepPicking(dt: number)
	if not picking then
		return
	end
	sincePick += dt
	if sincePick >= PICKUP_SECONDS then
		sincePick = 0
		pickUp(true)
	end
end

-- The middle button: takes the thing looked at into the hand. If a slot already holds it that
-- slot is chosen; otherwise it goes into the current slot, when the bag has one to give. A
-- machine is also turned the way the one looked at faces.
local function pickLooked()
	local found = if Screens.anyOpen() then nil else target()
	if not found then
		return
	end
	local entry: string? = nil
	local facing: number? = nil
	if found.model then
		entry = found.model:GetAttribute("Machine") :: any
		local turned = found.model:GetAttribute("Dir")
		facing = if Grid.isDir(turned) then turned :: number else nil
	else
		-- The server writes on each block what it is. Its look says nothing: textured blocks are
		-- all white underneath.
		local named = found.part:GetAttribute("Block")
		entry = if type(named) == "string" then named else nil
	end
	if not entry or not Defs.isPlaceable(entry) then
		return
	end
	local picked = Defs.Machines[entry]
	if picked and picked.hidden then
		return -- a tree or a growing crop is not something to hold
	end
	local slots = if hotbar.slots then hotbar.slots() else {}
	local what, index = HandLogic.pick(Stock, slots, entry, hotbar.bag, isCreative())
	if what == "select" and index then
		hotbar.select(index)
	elseif what == "assign" then
		local empty = table.find(slots, "")
		if empty then
			hotbar.select(empty)
		end
		hotbar.assign(entry)
	else
		UIKit.toast("가방에 " .. Defs.name(entry) .. "이(가) 없습니다")
		return
	end
	if facing then
		dir = facing
	end
end

-- The machine whose prompt should be on offer: the one pointed at, or on touch (where nothing is
-- pointed at between taps) the nearest one within a couple of cells.
local function aimedMachine(root: BasePart, near: { Model }): Model?
	if HandInput.mode() == "touch" then
		local best: Model? = nil
		local bestDistance = TOUCH_PROMPT_RANGE
		for _, model in near do
			local distance = (model:GetPivot().Position - root.Position).Magnitude
			if distance <= bestDistance then
				best, bestDistance = model, distance
			end
		end
		return best
	end
	local ray = HandInput.ray()
	if not ray then
		return nil
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignoreList()
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 400, params)
	local model = hit and hit.Instance:FindFirstAncestorOfClass("Model")
	return if model and model:GetAttribute("Machine") then model else nil
end

-- A machine prompt's reach is always this (MachineKit.prompt sets it). It is written here rather
-- than read back from the prompt, because what is read back may be this client's own zero.
local PROMPT_REACH = 10
-- The prompts each machine has.
local promptsOf: { [Model]: { at: number, list: { ProximityPrompt } } } = setmetatable({}, { __mode = "k" }) :: any

local function promptsFor(model: Model): { ProximityPrompt }
	local known = promptsOf[model]
	local now = os.clock()
	-- Looked up once, and again now and then in case the prompt arrived after the machine did.
	if known and (#known.list > 0 or now - known.at < 3) then
		return known.list
	end
	local list = {}
	for _, child in model:GetDescendants() do
		if child:IsA("ProximityPrompt") then
			table.insert(list, child)
		end
	end
	promptsOf[model] = { at = now, list = list }
	return list
end

-- A machine's F prompt is offered only for the machine the player is aiming at. Otherwise every
-- machine within ten studs would claim F, and nothing lying near a factory could be picked up.
-- This is done by pulling in the reach of the other prompts on this player's screen only; whether
-- a prompt is switched on at all stays the server's business.
local function gatePrompts(dt: number)
	sinceGate += dt
	if sinceGate < GATE_SECONDS then
		return
	end
	sinceGate = 0
	local _, root = character()
	if not root then
		return
	end
	local near: { Model } = {}
	for _, island in Workspace:GetChildren() do
		local machines = if string.sub(island.Name, 1, 7) == "Island_"
			then island:FindFirstChild("Machines")
			else nil
		if machines then
			for _, model in machines:GetChildren() do
				if
					model:IsA("Model")
					and (model:GetPivot().Position - root.Position).Magnitude <= PROMPT_SIGHT
				then
					if #promptsFor(model) > 0 then
						table.insert(near, model)
					end
				end
			end
		end
	end
	local aimed = aimedMachine(root, near)
	for _, model in near do
		for _, prompt in promptsFor(model) do
			local reach = if model == aimed then PROMPT_REACH else 0
			if prompt.MaxActivationDistance ~= reach then
				prompt.MaxActivationDistance = reach
			end
		end
	end
end

local function onInputBegan(input: InputObject, handledByUi: boolean)
	if handledByUi then
		return
	end
	if input.UserInputType == Enum.UserInputType.MouseButton3 then
		pickLooked()
	elseif input.KeyCode == Enum.KeyCode.R then
		dir = Grid.rotate(dir, 1)
	elseif input.KeyCode == Enum.KeyCode.Q then
		dropping = true
		sinceDrop = 0
		dropHeld()
	elseif input.KeyCode == Enum.KeyCode.LeftShift then
		setRunning(true)
	elseif input.KeyCode == Enum.KeyCode.F then
		picking = true
		sincePick = 0
		pickUp()
	elseif input.KeyCode == Enum.KeyCode.ButtonR1 or input.KeyCode == Enum.KeyCode.ButtonL1 then
		-- A gamepad has no number keys: the shoulder buttons step along the bar.
		local step = if input.KeyCode == Enum.KeyCode.ButtonR1 then 1 else -1
		hotbar.select((hotbar.selectedIndex() - 1 + step) % 10 + 1)
	elseif keys[input.KeyCode] then
		hotbar.select(keys[input.KeyCode])
	end
end

local function onInputEnded(input: InputObject)
	if input.KeyCode == Enum.KeyCode.Q then
		dropping = false
	elseif input.KeyCode == Enum.KeyCode.F then
		picking = false
	elseif input.KeyCode == Enum.KeyCode.LeftShift then
		setRunning(false)
	end
end

-- Buttons for players with no keyboard. ContextActionService draws them only on touch screens;
-- the same actions are given a gamepad button each.
local function bindButtons()
	local SINK = Enum.ContextActionResult.Sink
	local function held(state: Enum.UserInputState): boolean?
		if state == Enum.UserInputState.Begin then
			return true
		elseif state == Enum.UserInputState.End or state == Enum.UserInputState.Cancel then
			return false
		end
		return nil
	end

	ContextActionService:BindAction("FactoryDrop", function(_, state)
		local now = held(state)
		if now then
			dropping = true
			sinceDrop = 0
			dropHeld()
		elseif now == false then
			dropping = false
		end
		return SINK
	end, true, Enum.KeyCode.DPadDown)
	ContextActionService:SetTitle("FactoryDrop", "떨구기")

	ContextActionService:BindAction("FactoryPickup", function(_, state)
		local now = held(state)
		if now then
			picking = true
			sincePick = 0
			pickUp()
		elseif now == false then
			picking = false
		end
		return SINK
	end, true, Enum.KeyCode.DPadUp)
	ContextActionService:SetTitle("FactoryPickup", "줍기")

	-- Running is a switch here: there is no key to keep held.
	ContextActionService:BindAction("FactoryRun", function(_, state)
		if state == Enum.UserInputState.Begin then
			setRunning(not running)
		end
		return SINK
	end, true, Enum.KeyCode.ButtonL3)
	ContextActionService:SetTitle("FactoryRun", "달리기")

	-- Turning is only offered while there is a machine in the hand to turn.
	local turning = false
	local function offerTurn()
		local wanted = Defs.Machines[hotbar.selected()] ~= nil
		if wanted == turning then
			return
		end
		turning = wanted
		if wanted then
			ContextActionService:BindAction("FactoryTurn", function(_, state)
				if state == Enum.UserInputState.Begin then
					dir = Grid.rotate(dir, 1)
				end
				return SINK
			end, true, Enum.KeyCode.ButtonY)
			ContextActionService:SetTitle("FactoryTurn", "돌리기")
		else
			ContextActionService:UnbindAction("FactoryTurn")
		end
	end
	hotbar.onSelect(offerTurn)
	offerTurn()
end

function BuildController.init(hotbarUi)
	hotbar = hotbarUi
	makeGhost()
	HandInput.start()
	HandInput.onBegan(use)
	HandInput.onEnded(function()
		breaking = nil
		laying = nil
	end)
	UserInputService.InputBegan:Connect(onInputBegan)
	UserInputService.InputEnded:Connect(onInputEnded)
	RunService.RenderStepped:Connect(drawGhost)
	RunService.RenderStepped:Connect(keepBreaking)
	RunService.RenderStepped:Connect(keepLaying)
	RunService.RenderStepped:Connect(keepDropping)
	RunService.RenderStepped:Connect(keepPicking)
	RunService.RenderStepped:Connect(gatePrompts)
	ProximityPromptService.PromptShown:Connect(function()
		promptsShown += 1
	end)
	ProximityPromptService.PromptHidden:Connect(function()
		promptsShown = math.max(0, promptsShown - 1)
	end)
	-- A new body starts at walking pace; keep running if the switch is on.
	player.CharacterAdded:Connect(function(body)
		if running then
			local humanoid = body:WaitForChild("Humanoid", 5)
			if humanoid and humanoid:IsA("Humanoid") then
				humanoid.WalkSpeed = RUN_SPEED
			end
		end
	end)
	bindButtons()
end

return BuildController
