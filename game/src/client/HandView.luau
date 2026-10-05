-- What the player sees in their hand, and the swing when they use it.
-- Close in (first person) the thing held floats at the lower right of the view; from further out
-- it sits in the character's right hand and the arm swings. Everything here is only on this
-- player's screen: it is a picture of what the hotbar says, not something the server knows about.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local ModelBuilder = require(Shared:WaitForChild("ModelBuilder"))

local HandView = {}

local player = Players.LocalPlayer
local SWING_SECONDS = 0.28
local HELD_SIZE = 1.1 -- studs: machines and blocks are shrunk to about this
local FIRST_PERSON = 1.5 -- camera closer to its focus than this counts as first person
-- Where the held thing sits: relative to the camera, and relative to the right hand.
local IN_VIEW = CFrame.new(0.95, -0.8, -1.9) * CFrame.Angles(0, math.rad(-20), math.rad(-8))
local IN_HAND = CFrame.new(0, -0.35, -0.55) * CFrame.Angles(math.rad(-90), 0, 0)

type Piece = { part: BasePart, offset: CFrame }

local pieces: { Piece } = {}
local holder: Folder? = nil
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
			adopt(folder, centre * scale)
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

local function rightHand(character: Model): BasePart?
	local hand = character:FindFirstChild("RightHand") or character:FindFirstChild("Right Arm")
	return if hand and hand:IsA("BasePart") then hand else nil
end

local function shoulder(character: Model): Motor6D?
	local upper = character:FindFirstChild("RightUpperArm")
	local joint = upper and upper:FindFirstChild("RightShoulder")
	if not joint then
		local torso = character:FindFirstChild("Torso")
		joint = torso and torso:FindFirstChild("Right Shoulder")
	end
	return if joint and joint:IsA("Motor6D") then joint else nil
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
	local amount = swingAmount()
	local base: CFrame? = nil
	if isFirstPerson(camera) then
		base = camera.CFrame
			* IN_VIEW
			* CFrame.new(0, -0.25 * amount, -0.5 * amount)
			* CFrame.Angles(math.rad(-70) * amount, math.rad(15) * amount, 0)
	elseif character then
		local hand = rightHand(character)
		if hand then
			base = hand.CFrame * IN_HAND
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

-- Raises the right arm while something is held and swings it on use. The animation system writes
-- the joint every frame, so this has to be written after it, every frame.
local function poseArm()
	local character = player.Character
	local joint = character and shoulder(character)
	if not joint then
		return
	end
	local amount = swingAmount()
	local lift = if #pieces > 0 then math.rad(35) else 0
	local angle = lift + math.rad(75) * amount
	if angle == 0 then
		return
	end
	-- The two body types have their shoulder joints turned differently.
	if joint.Name == "RightShoulder" then
		joint.Transform = CFrame.Angles(angle, 0, 0)
	else
		joint.Transform = CFrame.Angles(0, 0, angle)
	end
end

-- Call when the player uses what is in their hand: placing, breaking, hitting, dropping.
function HandView.swing()
	swingAt = os.clock()
end

function HandView.init(hotbarUi)
	hotbar = hotbarUi
	hotbar.onSelect(function()
		build(hotbar.selected())
	end)
	build(hotbar.selected())
	-- After the camera has moved for this frame, so the held thing does not trail behind it.
	RunService:BindToRenderStep("HandView", Enum.RenderPriority.Camera.Value + 1, place)
	RunService.Stepped:Connect(poseArm)
end

return HandView
