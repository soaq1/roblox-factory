-- The windows that open over the game (palette, crafting, trade, shop). One is open at a time.
-- Each screen registers its frame here, optionally with a key that opens and closes it.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local SoundPlayer = require(script.Parent.SoundPlayer)

local Screens = {}

type Screen = { frame: GuiObject, key: Enum.KeyCode?, onOpen: (() -> ())?, onClose: (() -> ())? }

local screens: { [string]: Screen } = {}
local keyRuns: { [Enum.KeyCode]: () -> () } = {}
local changeRuns: { () -> () } = {}
local gui: ScreenGui? = nil

-- The one ScreenGui everything in this game is drawn in.
function Screens.gui(): ScreenGui
	if not gui then
		local made = Instance.new("ScreenGui")
		made.Name = "FactoryUI"
		made.ResetOnSpawn = false
		made.IgnoreGuiInset = false
		made.ZIndexBehavior = Enum.ZIndexBehavior.Sibling -- windows cover what they overlap
		made.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
		gui = made
	end
	return gui :: ScreenGui
end

function Screens.register(
	name: string,
	frame: GuiObject,
	key: Enum.KeyCode?,
	onOpen: (() -> ())?,
	onClose: (() -> ())?
)
	frame.Visible = false
	screens[name] = { frame = frame, key = key, onOpen = onOpen, onClose = onClose }
end

-- Runs `run` whenever a window opens or closes.
function Screens.onChange(run: () -> ())
	table.insert(changeRuns, run)
end

local function changed()
	for _, run in changeRuns do
		task.spawn(run)
	end
end

-- Runs `run` when a key is pressed outside of chat and text boxes.
function Screens.onKey(key: Enum.KeyCode, run: () -> ())
	keyRuns[key] = run
end

function Screens.isOpen(name: string): boolean
	local screen = screens[name]
	return screen ~= nil and screen.frame.Visible
end

function Screens.anyOpen(): boolean
	for _, screen in screens do
		if screen.frame.Visible then
			return true
		end
	end
	return false
end

function Screens.close(name: string)
	local screen = screens[name]
	if screen and screen.frame.Visible then
		screen.frame.Visible = false
		if screen.onClose then
			screen.onClose()
		end
		changed()
	end
end

function Screens.closeAll()
	for name in screens do
		Screens.close(name)
	end
end

function Screens.open(name: string)
	local screen = screens[name]
	if not screen then
		return
	end
	for other in screens do
		if other ~= name then
			Screens.close(other)
		end
	end
	if not screen.frame.Visible then
		SoundPlayer.play("open")
		screen.frame.Visible = true
		if screen.onOpen then
			screen.onOpen()
		end
		changed()
	end
end

function Screens.toggle(name: string)
	if Screens.isOpen(name) then
		Screens.close(name)
	else
		Screens.open(name)
	end
end

function Screens.init()
	UserInputService.InputBegan:Connect(function(input, handled)
		-- Keys typed into chat or a text box are text, not commands.
		if
			handled
			or input.UserInputType ~= Enum.UserInputType.Keyboard
			or UserInputService:GetFocusedTextBox()
		then
			return
		end
		local run = keyRuns[input.KeyCode]
		if run then
			run()
			return
		end
		for name, screen in screens do
			if screen.key == input.KeyCode then
				Screens.toggle(name)
				return
			end
		end
	end)
end

return Screens
