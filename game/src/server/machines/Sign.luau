-- A sign: the owner writes on it and the words show on both faces.
-- Roblox requires any text one player writes and others can read to pass through its filter, so
-- the words as typed are kept (and saved) but never shown: what is shown is the filtered copy,
-- made again every time the sign is built, and nothing at all if the filter cannot be reached.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextService = game:GetService("TextService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local SocialLogic = require(Shared.SocialLogic)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineActs = require(script.Parent.Parent.MachineActs)

local Sign = {}

local INK = Color3.fromRGB(58, 40, 22)
-- The board in the model: its middle above the ground, and its size (thin, tall, wide).
local BOARD_HEIGHT = 2.52
local BOARD_SIZE = Vector3.new(0.26, 1.4, 2.7)

local function face(board: Part, side: Enum.NormalId): TextLabel
	local gui = Instance.new("SurfaceGui")
	gui.Face = side
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 50
	gui.Parent = board
	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, -12, 1, -8)
	label.Position = UDim2.fromOffset(6, 4)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = INK
	label.TextScaled = true
	label.TextWrapped = true
	label.Text = ""
	label.Parent = gui
	-- Short text should not blow up to fill the whole board.
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = 36
	limit.MinTextSize = 8
	limit.Parent = label
	return label
end

local function show(machine, text: string)
	for _, label in machine.faces do
		label.Text = text
	end
end

-- Filters the typed words and puts the result on the faces. It waits on Roblox, so it runs on its
-- own; if the words change again meanwhile, the older answer is thrown away.
local function refresh(machine)
	machine.version += 1
	local version = machine.version
	local raw = machine.raw
	if raw == "" then
		show(machine, "")
		return
	end
	local owner = machine.island.owner
	task.spawn(function()
		local ok, shown = pcall(function()
			local result = TextService:FilterStringAsync(raw, owner.UserId, Enum.TextFilterContext.PublicChat)
			return result:GetNonChatStringForBroadcastAsync()
		end)
		if machine.version ~= version or not machine.model.Parent then
			return
		end
		show(machine, if ok and type(shown) == "string" then shown else "")
		if not ok then
			warn("sign text could not be filtered: " .. tostring(shown))
		end
	end)
end

function Sign.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)

	-- An unseen slab hugging the board, a hair thicker so the words sit just proud of it.
	local board = Instance.new("Part")
	board.Name = "Board"
	board.Anchored = true
	board.Transparency = 1
	board.CanCollide = false
	board.CanQuery = false
	board.CanTouch = false
	board.Size = BOARD_SIZE
	board.CFrame = machine.base * CFrame.new(0, -Config.CELL / 2 + BOARD_HEIGHT, 0)
	board.Parent = machine.model

	machine.faces = { face(board, Enum.NormalId.Right), face(board, Enum.NormalId.Left) }
	machine.raw = ""
	machine.version = 0

	Kit.prompt(machine, body, "글 쓰기", function(player)
		if player == machine.island.owner then
			MachineActs.show(player, machine, "sign", {
				text = machine.raw,
				chars = SocialLogic.SIGN_CHARS,
				lines = SocialLogic.SIGN_LINES,
			})
		end
	end)
end

function Sign.load(machine, saved)
	local text = SocialLogic.cleanSign(if type(saved) == "table" then saved.text else nil)
	if text and text ~= "" then
		machine.raw = text
		refresh(machine)
	end
end

function Sign.save(machine)
	return { text = machine.raw }
end

-- "write": the owner sets the words. Anyone else's request is ignored.
function Sign.act(machine, player: Player, action: string, arg: any)
	if action ~= "write" or player ~= machine.island.owner then
		return
	end
	local text = SocialLogic.cleanSign(arg)
	if not text then
		return
	end
	machine.raw = text
	refresh(machine)
end

return Sign
