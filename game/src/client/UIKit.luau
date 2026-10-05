-- The pieces every screen is built from, so they all look alike.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local ModelBuilder = require(Shared:WaitForChild("ModelBuilder"))
local Stock = require(Shared:WaitForChild("Stock"))(Defs)
local Screens = require(script.Parent.Screens)

local UIKit = {}

UIKit.Stock = Stock
UIKit.BACK = Color3.fromRGB(28, 30, 34)
UIKit.PANEL = Color3.fromRGB(36, 39, 44)
UIKit.LINE = Color3.fromRGB(70, 76, 85)
UIKit.TEXT = Color3.fromRGB(233, 234, 236)
UIKit.DIM = Color3.fromRGB(154, 160, 168)
UIKit.PICK = Color3.fromRGB(240, 180, 41)
UIKit.GOOD = Color3.fromRGB(127, 209, 139)
UIKit.BAD = Color3.fromRGB(229, 138, 128)

local toastLabel: TextLabel? = nil
local toastToken = 0

local function rgb(c: { number }): Color3
	return Color3.fromRGB(c[1], c[2], c[3])
end

function UIKit.round(parent: Instance, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

function UIKit.stroke(parent: Instance, color: Color3?, thickness: number?): UIStroke
	local stroke = Instance.new("UIStroke")
	stroke.Color = color or UIKit.LINE
	stroke.Thickness = thickness or 1
	stroke.Parent = parent
	return stroke
end

function UIKit.label(parent: Instance, text: string, size: number): TextLabel
	local item = Instance.new("TextLabel")
	item.BackgroundTransparency = 1
	item.Font = Enum.Font.GothamMedium
	item.TextSize = size
	item.TextColor3 = UIKit.TEXT
	item.TextWrapped = true
	item.Text = text
	item.Parent = parent
	return item
end

function UIKit.button(parent: Instance, text: string, size: number): TextButton
	local item = Instance.new("TextButton")
	item.AutoButtonColor = true
	item.BackgroundColor3 = UIKit.PANEL
	item.BorderSizePixel = 0
	item.Font = Enum.Font.GothamMedium
	item.TextSize = size
	item.TextColor3 = UIKit.TEXT
	item.Text = text
	item.Parent = parent
	UIKit.round(item, 6)
	return item
end

-- A box to type into. `numbersOnly` strips everything but digits as it is typed.
function UIKit.input(parent: Instance, placeholder: string, size: number, numbersOnly: boolean?): TextBox
	local box = Instance.new("TextBox")
	box.BackgroundColor3 = UIKit.PANEL
	box.BorderSizePixel = 0
	box.Font = Enum.Font.GothamMedium
	box.TextSize = size
	box.TextColor3 = UIKit.TEXT
	box.PlaceholderText = placeholder
	box.PlaceholderColor3 = UIKit.DIM
	box.Text = ""
	box.ClearTextOnFocus = false
	box.Parent = parent
	UIKit.round(box, 6)
	if numbersOnly then
		box:GetPropertyChangedSignal("Text"):Connect(function()
			local digits = string.gsub(box.Text, "%D", "")
			if digits ~= box.Text then
				box.Text = digits
			end
		end)
	end
	return box
end

-- A scrolling area whose contents are laid out in a column (`cell` nil) or a grid of `cell` size.
function UIKit.scroller(parent: Instance, cell: Vector2?, gap: number?): ScrollingFrame
	local frame = Instance.new("ScrollingFrame")
	frame.BackgroundTransparency = 1
	frame.BorderSizePixel = 0
	frame.ScrollBarThickness = 6
	frame.CanvasSize = UDim2.new()
	frame.AutomaticCanvasSize = Enum.AutomaticSize.Y
	frame.Parent = parent
	if cell then
		local layout = Instance.new("UIGridLayout")
		layout.CellSize = UDim2.fromOffset(cell.X, cell.Y)
		layout.CellPadding = UDim2.fromOffset(gap or 8, gap or 8)
		layout.SortOrder = Enum.SortOrder.LayoutOrder
		layout.Parent = frame
	else
		local layout = Instance.new("UIListLayout")
		layout.Padding = UDim.new(0, gap or 5)
		layout.SortOrder = Enum.SortOrder.LayoutOrder
		layout.Parent = frame
	end
	return frame
end

-- Removes everything drawn in a frame but keeps its layout objects.
function UIKit.clear(frame: Instance)
	for _, child in frame:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
end

local function swatch(frame: Instance, color: Color3, top: Color3?, transparency: number, radius: number)
	local side = Instance.new("Frame")
	side.AnchorPoint = Vector2.new(0.5, 0.5)
	side.Position = UDim2.fromScale(0.5, 0.5)
	side.Size = if top then UDim2.fromScale(0.62, 0.78) else UDim2.fromScale(0.5, 0.62)
	side.BorderSizePixel = 0
	side.BackgroundColor3 = color
	side.BackgroundTransparency = transparency
	side.Parent = frame
	if top then
		local band = Instance.new("Frame")
		band.Size = UDim2.fromScale(1, 0.28)
		band.BorderSizePixel = 0
		band.BackgroundColor3 = top
		band.BackgroundTransparency = transparency
		band.Parent = side
	else
		UIKit.round(side, radius)
	end
end

-- A small view of a model, seen from the front corner, framed to fit.
local function modelPicture(parent: Instance, id: string)
	local view = Instance.new("ViewportFrame")
	view.Size = UDim2.fromScale(1, 1)
	view.BackgroundTransparency = 1
	view.Ambient = Color3.fromRGB(175, 175, 175)
	view.LightColor = Color3.fromRGB(255, 255, 255)
	view.LightDirection = Vector3.new(-0.5, -1, -0.7)
	ModelBuilder.build(view, CFrame.new(), id)

	local centre, size = ModelBuilder.bounds(id)
	local camera = Instance.new("Camera")
	camera.FieldOfView = 20
	camera.CFrame = CFrame.lookAt(
		centre + Vector3.new(0.8, 0.7, 1).Unit * (size.Magnitude / 2 / math.tan(math.rad(10))),
		centre
	)
	camera.Parent = view
	view.CurrentCamera = camera
	view.Parent = parent
end

local function machinePicture(parent: Instance, def)
	modelPicture(parent, if def.stages then def.stages[#def.stages] else def.icon)
end

-- A loose item: its model if it has one, otherwise a lump in its colour.
local function itemPicture(frame: Instance, id: string)
	if ModelBuilder.has("item_" .. id) then
		modelPicture(frame, "item_" .. id)
	else
		local def = Defs.Items[id]
		swatch(frame, rgb(def.color), nil, 0, if def.ball then 100 else 5)
	end
end

-- Fills a frame with the picture of anything: a palette entry ("smelter", "grass", "item:log")
-- or a bag key ("smelter", "log", "block:grass").
function UIKit.picture(frame: Instance, entry: string)
	frame:ClearAllChildren()
	local item = Defs.itemOf(entry)
	local block = Stock.blockOf(entry)
	if item then
		itemPicture(frame, item)
	elseif block then
		local def = Defs.Blocks[block]
		swatch(frame, rgb(def.color), rgb(def.top), def.transparency, 0)
	elseif Defs.Machines[entry] then
		machinePicture(frame, Defs.Machines[entry])
	elseif Defs.Blocks[entry] and not Defs.Items[entry] then
		local def = Defs.Blocks[entry]
		swatch(frame, rgb(def.color), rgb(def.top), def.transparency, 0)
	elseif Defs.Items[entry] then
		itemPicture(frame, entry)
	end
end

-- A tile: a picture with a name underneath. The picture frame is named "Picture", the label "Name".
function UIKit.tile(parent: Instance, entry: string, width: number, height: number, name: string?): Frame
	local frame = Instance.new("Frame")
	frame.Size = UDim2.fromOffset(width, height)
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	UIKit.round(frame, 8)
	UIKit.stroke(frame)
	local art = Instance.new("Frame")
	art.Name = "Picture"
	art.BackgroundTransparency = 1
	art.Size = UDim2.new(1, 0, 1, -26)
	art.Parent = frame
	local text = UIKit.label(frame, name or (if entry == "" then "" else Defs.name(entry)), 11)
	text.Name = "Name"
	text.Size = UDim2.new(1, -6, 0, 26)
	text.Position = UDim2.new(0, 3, 1, -27)
	UIKit.picture(art, entry)
	frame.Parent = parent
	return frame
end

-- An unseen button covering a frame, for making a whole tile clickable.
function UIKit.cover(frame: Instance, run: () -> ()): TextButton
	local press = Instance.new("TextButton")
	press.BackgroundTransparency = 1
	press.Text = ""
	press.Size = UDim2.fromScale(1, 1)
	press.ZIndex = 5
	press.Parent = frame
	press.Activated:Connect(run)
	return press
end

-- A window in the middle of the screen with a title and a close button, registered as a screen.
-- Returns the window and the area below the title to put things in.
function UIKit.window(
	name: string,
	title: string,
	width: number,
	height: number,
	key: Enum.KeyCode?,
	onOpen: (() -> ())?,
	onClose: (() -> ())?
): (Frame, Frame)
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.45)
	frame.Size = UDim2.fromOffset(width, height)
	frame.BackgroundColor3 = UIKit.BACK
	frame.BorderSizePixel = 0
	frame.Parent = Screens.gui()
	UIKit.round(frame, 12)
	-- Shrinks the window to fit small screens.
	local fit = Instance.new("UIScale")
	fit.Parent = frame
	local function refit()
		local camera = Workspace.CurrentCamera
		if camera then
			local view = camera.ViewportSize
			-- leave room for the hotbar below and the read-outs above
			fit.Scale = math.clamp(math.min((view.X - 40) / width, (view.Y - 190) / height), 0.5, 1)
		end
	end
	refit()
	if Workspace.CurrentCamera then
		Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(refit)
	end

	local heading = UIKit.label(frame, title, 16)
	heading.Name = "Title"
	heading.TextXAlignment = Enum.TextXAlignment.Left
	heading.Position = UDim2.fromOffset(16, 10)
	heading.Size = UDim2.new(1, -70, 0, 26)

	local close = UIKit.button(frame, "닫기", 13)
	close.Size = UDim2.fromOffset(46, 26)
	close.Position = UDim2.new(1, -58, 0, 10)
	close.Activated:Connect(function()
		Screens.close(name)
	end)

	local body = Instance.new("Frame")
	body.Name = "Body"
	body.BackgroundTransparency = 1
	body.Position = UDim2.fromOffset(14, 46)
	body.Size = UDim2.new(1, -28, 1, -60)
	body.Parent = frame

	Screens.register(name, frame, key, onOpen, onClose)
	return frame, body
end

-- A line of text at the top of the screen that goes away after a few seconds.
function UIKit.toast(text: string)
	local label = toastLabel
	if not label then
		label = UIKit.label(Screens.gui(), "", 15)
		label.AnchorPoint = Vector2.new(0.5, 0)
		label.Position = UDim2.new(0.5, 0, 0, 40)
		label.Size = UDim2.fromOffset(680, 48)
		label.BackgroundTransparency = 0.15
		label.BackgroundColor3 = UIKit.PANEL
		label.ZIndex = 20
		UIKit.round(label, 8)
		toastLabel = label
	end
	toastToken += 1
	local token = toastToken
	label.Text = text
	label.Visible = true
	task.delay(5, function()
		if token == toastToken then
			label.Visible = false
		end
	end)
end

-- Numbers with thousands separators: 12345 -> "12,345".
function UIKit.number(n: number): string
	local grouped = string.gsub(string.reverse(tostring(math.floor(n))), "(%d%d%d)", "%1,")
	local out = string.gsub(string.reverse(grouped), "^,", "")
	return out
end

return UIKit
