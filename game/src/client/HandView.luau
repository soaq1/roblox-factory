-- What the player sees in their hand, and the swing when they use it.
-- Close in (first person) the thing held floats at the lower right of the view; from further out
-- it sits in the character's right hand. The thing itself is only on this player's screen.
-- The arm is moved the way Roblox moves it for any held tool: an empty Tool is put in the character
-- while something is held, and Roblox's own animation script raises the arm for it and swings it
-- when asked. Those animations are also what other players see.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local ModelBuilder = require(Shared:WaitForChild("ModelBuilder"))
local ToolLogic = require(Shared:WaitForChild("ToolLogic"))

local HandView = {}

local player = Players.LocalPlayer
local SWING_SECONDS = 0.28
local HELD_SIZE = 1.1 -- studs: machines and blocks are shrunk to about this
local FIRST_PERSON = 1.5 -- camera closer to its focus than this counts as first person
-- A tool is modelled standing up with its head across it, flat towards the front. Held, it is
-- turned so the head points away from the holder and is seen edge-on, the way a pickaxe is swung.
local TURNED = CFrame.Angles(0, math.rad(78), 0)
-- Where the grip sits in first person, relative to the camera, and how far the top leans away.
local VIEW_AT = Vector3.new(0.85, -1.15, -1.55)
local VIEW_LEAN = math.rad(-22)
local VIEW_SWING = math.rad(-62) -- how much further it tips at the middle of a swing

type Piece = { part: BasePart, offset: CFrame }

local pieces: { Piece } = {}
local holder: Folder? = nil
local held: Tool? = nil -- the empty Tool that makes Roblox raise and swing the arm
local swingAt = -10
local hotbar

local function clear()
	if holder then
		holder:Destroy()
		holder = nil
	end
	table.clear(pieces)
end

-- Takes over a freshly built folder of parts: remembers where each sits relative to `centre`.
local function adopt(folder: Folder, centre: Vector3)
	holder = folder
	for _, part in folder:GetChildren() do
		if part:IsA("BasePart") then
			part.CanCollide = false
			part.CanQuery = false
			part.CanTouch = false
			part.CastShadow = false
			table.insert(pieces, { part = part, offset = CFrame.new(-centre) * part.CFrame })
		end
	end
end

local function blockPart(parent: Instance, color: { number }, size: Vector3, at: Vector3)
	local part = Instance.new("Part")
	part.Anchored = true
	part.Material = Enum.Material.SmoothPlastic
	part.Color = Color3.fromRGB(color[1], color[2], color[3])
	part.Size = size
	part.Position = at
	part.Parent = parent
end

-- Builds the thing for a hotbar entry, about HELD_SIZE across, around the origin.
local function build(entry: string)
	clear()
	local camera = Workspace.CurrentCamera
	if entry == "" or not camera then
		return
	end
	local item = Defs.itemOf(entry)
	local machine = Defs.Machines[entry]
	local block = Defs.Blocks[entry]
	local id: string? = nil
	if item and ModelBuilder.has("item_" .. item) then
		id = "item_" .. item
	elseif machine then
		id = if machine.stages then machine.stages[1] else machine.icon
	end
	if id then
		local centre, size = ModelBuilder.bounds(id)
		-- Tools and items are already hand-sized; machines are shrunk to fit a hand.
		local scale = if item then 1 else HELD_SIZE / math.max(size.X, size.Y, size.Z)
		local folder = ModelBuilder.build(camera, CFrame.new(), id, scale)
		if folder then
			folder.Name = "Held"
			-- A tool is held low on its handle, so it swings about the hand; anything else is
			-- held by its middle.
			local grip = centre * scale
			if item and ToolLogic.parse(item) then
				grip -= Vector3.new(0, size.Y * 0.3, 0)
			end
			adopt(folder, grip)
		end
	elseif block or item then
		local folder = Instance.new("Folder")
		folder.Name = "Held"
		if block then
			local side = HELD_SIZE * 0.7
			blockPart(folder, block.color, Vector3.new(side, side, side), Vector3.zero)
			blockPart(
				folder,
				block.top,
				Vector3.new(side + 0.02, side * 0.15, side + 0.02),
				Vector3.new(0, side * 0.43, 0)
			)
		else
			blockPart(folder, Defs.Items[item :: string].color, Vector3.new(0.5, 0.5, 0.5), Vector3.zero)
		end
		folder.Parent = camera
		adopt(folder, Vector3.zero)
	end
end

-- 0 at rest, rising to 1 mid-swing and back to 0.
local function swingAmount(): number
	local t = (os.clock() - swingAt) / SWING_SECONDS
	if t < 0 or t > 1 then
		return 0
	end
	return math.sin(t * math.pi)
end

-- Where a held thing sits in the right hand: Roblox marks the spot on every character.
local function gripFrame(character: Model): CFrame?
	local hand = character:FindFirstChild("RightHand")
	local spot = hand and hand:FindFirstChild("RightGripAttachment")
	if spot and spot:IsA("Attachment") then
		return spot.WorldCFrame
	end
	-- the older body type has no such mark: the end of the right arm, turned the same way
	local arm = character:FindFirstChild("Right Arm")
	if arm and arm:IsA("BasePart") then
		return arm.CFrame * CFrame.new(0, -1, 0) * CFrame.Angles(-math.pi / 2, 0, 0)
	end
	return nil
end

local function isFirstPerson(camera: Camera): boolean
	return (camera.Focus.Position - camera.CFrame.Position).Magnitude < FIRST_PERSON
end

-- Puts the held thing where it belongs for this frame.
local function place()
	local camera = Workspace.CurrentCamera
	local character = player.Character
	if #pieces == 0 or not camera then
		return
	end
	local base: CFrame? = nil
	if isFirstPerson(camera) then
		local amount = swingAmount()
		base = camera.CFrame
			* CFrame.new(VIEW_AT + Vector3.new(0, -0.15 * amount, -0.35 * amount))
			* CFrame.Angles(VIEW_LEAN + VIEW_SWING * amount, 0, 0)
			* TURNED
	elseif character then
		local grip = gripFrame(character)
		if grip then
			base = grip * TURNED
		end
	end
	for _, piece in pieces do
		if base then
			piece.part.CFrame = base * piece.offset
			piece.part.LocalTransparencyModifier = 0
		else
			piece.part.LocalTransparencyModifier = 1
		end
	end
end

-- Keeps an empty Tool in the character while something is held, and none while the hand is empty.
-- Roblox's animation script sees the Tool and holds the arm out for it.
local function holdArm()
	local character = player.Character
	local wanted = #pieces > 0 and character ~= nil
	if wanted and character then
		if not held or held.Parent ~= character then
			if held then
				held:Destroy()
			end
			local tool = Instance.new("Tool")
			tool.Name = "Held"
			tool.RequiresHandle = false
			tool.CanBeDropped = false
			tool.ManualActivationOnly = true
			tool.Parent = character
			held = tool
		end
	elseif held then
		held:Destroy()
		held = nil
	end
end

-- Call when the player uses what is in their hand: placing, breaking, hitting, dropping.
function HandView.swing()
	swingAt = os.clock()
	-- Roblox's animation script looks for this note on the held Tool and plays its slash.
	if held and not held:FindFirstChild("toolanim") then
		local note = Instance.new("StringValue")
		note.Name = "toolanim"
		note.Value = "Slash"
		note.Parent = held
	end
end

function HandView.init(hotbarUi)
	hotbar = hotbarUi
	hotbar.onSelect(function()
		build(hotbar.selected())
		holdArm()
	end)
	build(hotbar.selected())
	holdArm()
	-- a new body after a fall or a death needs the Tool again
	player.CharacterAdded:Connect(function()
		held = nil
		task.defer(holdArm)
	end)
	-- After the camera has moved for this frame, so the held thing does not trail behind it.
	RunService:BindToRenderStep("HandView", Enum.RenderPriority.Camera.Value + 1, place)
end

return HandView
