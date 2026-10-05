-- One answer to "where is the player pointing, and are they pressing use?" whatever they play on.
-- A mouse points with the cursor and uses with the left button. A finger points where it last
-- touched the world: a tap is one use, a long press is a held use. A gamepad points at the middle
-- of the screen and uses with the right trigger. BuildController and WorldController both listen
-- here, so neither needs to know which of the three it is.
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Screens = require(script.Parent.Screens)

local HandInput = {}

local mode = "mouse" -- "mouse", "touch" or "gamepad"
local touchPoint: Vector2? = nil
local down = false
local started = false
local dot: Frame? = nil
local beganRuns: { () -> () } = {}
local endedRuns: { () -> () } = {}

-- Which kind of input was used last: "mouse", "touch" or "gamepad".
function HandInput.mode(): string
	return mode
end

-- Is use being held right now?
function HandInput.isDown(): boolean
	return down
end

-- The line from the eye through whatever the player is pointing at.
function HandInput.ray(): Ray?
	local camera = Workspace.CurrentCamera
	if not camera then
		return nil
	end
	if mode == "touch" then
		if not touchPoint then
			return nil
		end
		-- Touch positions leave out the top bar, and ScreenPointToRay allows for that.
		return camera:ScreenPointToRay(touchPoint.X, touchPoint.Y)
	elseif mode == "gamepad" then
		local view = camera.ViewportSize
		return camera:ViewportPointToRay(view.X / 2, view.Y / 2)
	end
	local mouse = UserInputService:GetMouseLocation()
	return camera:ViewportPointToRay(mouse.X, mouse.Y)
end

-- Runs when use is pressed. A tap counts as a press followed at once by a release.
function HandInput.onBegan(run: () -> ())
	table.insert(beganRuns, run)
end

function HandInput.onEnded(run: () -> ())
	table.insert(endedRuns, run)
end

local function fire(runs: { () -> () })
	for _, run in runs do
		task.spawn(run)
	end
end

local function press()
	down = true
	fire(beganRuns)
end

local function release()
	if down then
		down = false
		fire(endedRuns)
	end
end

local function setMode(now: string)
	mode = now
	if dot then
		dot.Visible = now == "gamepad"
	end
end

local function watchKind(kind: Enum.UserInputType)
	if kind == Enum.UserInputType.Touch then
		setMode("touch")
	elseif kind == Enum.UserInputType.Gamepad1 then
		setMode("gamepad")
	elseif
		kind == Enum.UserInputType.MouseMovement
		or kind == Enum.UserInputType.MouseButton1
		or kind == Enum.UserInputType.MouseButton2
		or kind == Enum.UserInputType.Keyboard
	then
		setMode("mouse")
	end
end

-- Safe to call more than once; whichever controller starts first sets it up.
function HandInput.start()
	if started then
		return
	end
	started = true

	-- A small dot marks the aim point for a gamepad, which has no cursor.
	local mark = Instance.new("Frame")
	mark.Name = "AimDot"
	mark.AnchorPoint = Vector2.new(0.5, 0.5)
	mark.Position = UDim2.fromScale(0.5, 0.5)
	mark.Size = UDim2.fromOffset(6, 6)
	mark.BackgroundColor3 = Color3.new(1, 1, 1)
	mark.BackgroundTransparency = 0.2
	mark.BorderSizePixel = 0
	mark.Visible = false
	mark.Parent = Screens.gui()
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(1, 0)
	corner.Parent = mark
	dot = mark

	watchKind(UserInputService:GetLastInputType())
	UserInputService.LastInputTypeChanged:Connect(watchKind)

	UserInputService.InputBegan:Connect(function(input, handledByUi)
		if handledByUi then
			return
		end
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			setMode("mouse")
			press()
		elseif input.KeyCode == Enum.KeyCode.ButtonR2 then
			setMode("gamepad")
			press()
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.KeyCode == Enum.KeyCode.ButtonR2
		then
			release()
		end
	end)

	UserInputService.TouchTapInWorld:Connect(function(position, handledByUi)
		if handledByUi then
			return
		end
		setMode("touch")
		touchPoint = position
		press()
		release()
	end)
	UserInputService.TouchLongPress:Connect(function(positions, state, handledByUi)
		if state == Enum.UserInputState.Begin then
			if handledByUi or not positions[1] then
				return
			end
			setMode("touch")
			touchPoint = positions[1]
			press()
		elseif state == Enum.UserInputState.Change then
			if down and positions[1] then
				touchPoint = positions[1]
			end
		else
			release()
		end
	end)
end

return HandInput
