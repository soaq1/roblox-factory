-- The nine quick slots, the creative palette, and the bag read-out.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Defs = require(Shared:WaitForChild("Defs"))
local ModelBuilder = require(Shared:WaitForChild("ModelBuilder"))
local Net = require(Shared:WaitForChild("Net"))
local Stock = require(Shared:WaitForChild("Stock"))(Defs)

local HotbarUI = {}

local SLOT = 70
local TILE = 96
local BACK = Color3.fromRGB(28, 30, 34)
local PANEL = Color3.fromRGB(36, 39, 44)
local LINE = Color3.fromRGB(70, 76, 85)
local TEXT = Color3.fromRGB(233, 234, 236)
local DIM = Color3.fromRGB(154, 160, 168)
local PICK = Color3.fromRGB(240, 180, 41)

local slots = table.clone(Defs.DefaultHotbar)
local selected = 1
local slotFrames: { Frame } = {}
local palette: Frame
local groupList: ScrollingFrame
local tileGrid: ScrollingFrame
local tabButtons: { [string]: TextButton } = {}
local currentTab = Defs.Tabs[1]
local bagLabel: TextLabel
local stateLabel: TextLabel
local toast: TextLabel
local toastToken = 0

local function rgb(c: { number }): Color3
	return Color3.fromRGB(c[1], c[2], c[3])
end

local function round(parent: Instance, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function label(parent: Instance, text: string, size: number): TextLabel
	local item = Instance.new("TextLabel")
	item.BackgroundTransparency = 1
	item.Font = Enum.Font.GothamMedium
	item.TextSize = size
	item.TextColor3 = TEXT
	item.TextWrapped = true
	item.Text = text
	item.Parent = parent
	return item
end

local function button(parent: Instance, text: string, size: number): TextButton
	local item = Instance.new("TextButton")
	item.AutoButtonColor = false
	item.BackgroundColor3 = PANEL
	item.BorderSizePixel = 0
	item.Font = Enum.Font.GothamMedium
	item.TextSize = size
	item.TextColor3 = TEXT
	item.Text = text
	item.Parent = parent
	round(item, 6)
	return item
end

-- A picture of a machine: its catalogue model seen from the front corner.
local function machinePicture(parent: Instance, def)
	local view = Instance.new("ViewportFrame")
	view.Size = UDim2.fromScale(1, 1)
	view.BackgroundTransparency = 1
	view.Ambient = Color3.fromRGB(175, 175, 175)
	view.LightColor = Color3.fromRGB(255, 255, 255)
	view.LightDirection = Vector3.new(-0.5, -1, -0.7)
	local shown = if def.stages then def.stages[#def.stages] else def.icon
	ModelBuilder.build(view, CFrame.new(), shown)

	local height = math.max(def.height, 1.5)
	local centre = Vector3.new(0, -Config.CELL / 2 + height / 2, 0)
	local radius = Vector3.new(def.sx * Config.CELL, height, def.sz * Config.CELL).Magnitude / 2
	local camera = Instance.new("Camera")
	camera.FieldOfView = 20
	camera.CFrame =
		CFrame.lookAt(centre + Vector3.new(0.8, 0.7, 1).Unit * (radius / math.tan(math.rad(10))), centre)
	camera.Parent = view
	view.CurrentCamera = camera
	view.Parent = parent
end

-- Fills a picture frame for any palette entry.
local function picture(frame: Frame, entry: string)
	frame:ClearAllChildren()
	local item = Defs.itemOf(entry)
	if item then
		-- loose items: a small lump in the item's colour
		local def = Defs.Items[item]
		local lump = Instance.new("Frame")
		lump.AnchorPoint = Vector2.new(0.5, 0.5)
		lump.Position = UDim2.fromScale(0.5, 0.5)
		lump.Size = UDim2.fromScale(0.5, 0.62)
		lump.BorderSizePixel = 0
		lump.BackgroundColor3 = rgb(def.color)
		lump.Parent = frame
		round(lump, if def.ball then 100 else 5)
	elseif Defs.Blocks[entry] then
		-- blocks: the side colour with the top colour as a band above it
		local def = Defs.Blocks[entry]
		local side = Instance.new("Frame")
		side.AnchorPoint = Vector2.new(0.5, 0.5)
		side.Position = UDim2.fromScale(0.5, 0.5)
		side.Size = UDim2.fromScale(0.62, 0.78)
		side.BorderSizePixel = 0
		side.BackgroundColor3 = rgb(def.color)
		side.BackgroundTransparency = def.transparency
		side.Parent = frame
		local top = Instance.new("Frame")
		top.Size = UDim2.fromScale(1, 0.28)
		top.BorderSizePixel = 0
		top.BackgroundColor3 = rgb(def.top)
		top.BackgroundTransparency = def.transparency
		top.Parent = side
	elseif Defs.Machines[entry] then
		machinePicture(frame, Defs.Machines[entry])
	end
end

-- A tile showing one palette entry: its picture with the name underneath.
local function tile(parent: Instance, entry: string, width: number, height: number): Frame
	local frame = Instance.new("Frame")
	frame.Size = UDim2.fromOffset(width, height)
	frame.BackgroundColor3 = PANEL
	frame.BorderSizePixel = 0
	round(frame, 8)
	local stroke = Instance.new("UIStroke")
	stroke.Color = LINE
	stroke.Thickness = 1
	stroke.Parent = frame
	local art = Instance.new("Frame")
	art.Name = "Picture"
	art.BackgroundTransparency = 1
	art.Size = UDim2.new(1, 0, 1, -26)
	art.Parent = frame
	local name = label(frame, Defs.name(entry), 11)
	name.Name = "Name"
	name.Size = UDim2.new(1, -6, 0, 26)
	name.Position = UDim2.new(0, 3, 1, -27)
	picture(art, entry)
	frame.Parent = parent
	return frame
end

-- Machines that are only a model for now get a small tag saying so.
local function tagIfModelOnly(frame: Frame, entry: string)
	local def = Defs.Machines[entry]
	if def and def.behavior == "decor" then
		local tag = label(frame, "모양만", 10)
		tag.Size = UDim2.fromOffset(40, 14)
		tag.Position = UDim2.new(1, -43, 0, 3)
		tag.TextColor3 = DIM
		tag.BackgroundTransparency = 0.2
		tag.BackgroundColor3 = BACK
		round(tag, 4)
	end
end

local function redrawSlot(i: number)
	local frame = slotFrames[i]
	picture(frame:FindFirstChild("Picture") :: Frame, slots[i])
	local name = frame:FindFirstChild("Name") :: TextLabel
	name.Text = Defs.name(slots[i])
end

local function redrawSelection()
	for i, frame in slotFrames do
		local stroke = frame:FindFirstChildOfClass("UIStroke") :: UIStroke
		stroke.Color = if i == selected then PICK else LINE
		stroke.Thickness = if i == selected then 3 else 1
	end
end

function HotbarUI.selected(): string
	return slots[selected]
end

function HotbarUI.select(index: number)
	if index >= 1 and index <= #slots then
		selected = index
		redrawSelection()
	end
end

function HotbarUI.isPaletteOpen(): boolean
	return palette.Visible
end

function HotbarUI.notify(text: string)
	toastToken += 1
	local token = toastToken
	toast.Text = text
	toast.Visible = true
	task.delay(5, function()
		if token == toastToken then
			toast.Visible = false
		end
	end)
end

local function showBag(bag: { [string]: number })
	local parts = {}
	for id, count in bag do
		table.insert(parts, Stock.name(id) .. " " .. count)
	end
	table.sort(parts)
	bagLabel.Text = if #parts > 0
		then "가방: " .. table.concat(parts, "  ·  ")
		else "가방: 비어 있음"
end

local function showState(state: { mode: string, coins: number })
	stateLabel.Text = (if state.mode == "survival" then "생존" else "크리에이티브")
		.. " · "
		.. state.coins
		.. "코인"
end

local function clear(frame: Instance)
	for _, child in frame:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
end

-- Shows the entries of one group in the right-hand grid.
local function showGroup(index: number)
	clear(tileGrid)
	tileGrid.CanvasPosition = Vector2.zero
	for order, entry in Defs.Palette[index].ids do
		local frame = tile(tileGrid, entry, TILE, TILE)
		frame.LayoutOrder = order
		tagIfModelOnly(frame, entry)
		local press = Instance.new("TextButton")
		press.BackgroundTransparency = 1
		press.Text = ""
		press.Size = UDim2.fromScale(1, 1)
		press.ZIndex = 5
		press.Parent = frame
		press.Activated:Connect(function()
			slots[selected] = entry
			redrawSlot(selected)
			local def = Defs.Machines[entry]
			if def and def.note ~= "" then
				HotbarUI.notify(def.name .. ": " .. def.note)
			end
		end)
	end
	for _, child in groupList:GetChildren() do
		if child:IsA("TextButton") then
			child.BackgroundColor3 = if child.LayoutOrder == index then LINE else PANEL
		end
	end
end

-- Shows the groups of one tab in the left-hand list and opens the first of them.
local function showTab(tab: string)
	currentTab = tab
	clear(groupList)
	local first: number? = nil
	for index, group in Defs.Palette do
		if group.tab == tab then
			first = first or index
			local item = button(groupList, group.name .. "  " .. #group.ids, 13)
			item.Size = UDim2.new(1, -6, 0, 30)
			item.LayoutOrder = index
			item.Activated:Connect(function()
				showGroup(index)
			end)
		end
	end
	for name, item in tabButtons do
		item.BackgroundColor3 = if name == tab then LINE else PANEL
	end
	if first then
		showGroup(first)
	end
end

function HotbarUI.togglePalette()
	palette.Visible = not palette.Visible
	if palette.Visible and #tileGrid:GetChildren() <= 1 then
		showTab(currentTab)
	end
end

local function buildPalette(gui: ScreenGui)
	palette = Instance.new("Frame")
	palette.AnchorPoint = Vector2.new(0.5, 0.5)
	palette.Position = UDim2.fromScale(0.5, 0.45)
	palette.Size = UDim2.fromOffset(760, 440)
	palette.BackgroundColor3 = BACK
	palette.BorderSizePixel = 0
	palette.Visible = false
	palette.Parent = gui
	round(palette, 12)

	local x = 14
	for _, tab in Defs.Tabs do
		local item = button(palette, tab, 15)
		item.Size = UDim2.fromOffset(90, 30)
		item.Position = UDim2.fromOffset(x, 12)
		item.Activated:Connect(function()
			showTab(tab)
		end)
		tabButtons[tab] = item
		x += 96
	end
	local title = label(palette, "고르면 지금 선택된 칸에 들어갑니다 · E로 닫기", 13)
	title.TextColor3 = DIM
	title.TextXAlignment = Enum.TextXAlignment.Right
	title.Size = UDim2.new(1, -x - 20, 0, 30)
	title.Position = UDim2.fromOffset(x, 12)

	groupList = Instance.new("ScrollingFrame")
	groupList.BackgroundTransparency = 1
	groupList.BorderSizePixel = 0
	groupList.Position = UDim2.fromOffset(14, 54)
	groupList.Size = UDim2.new(0, 170, 1, -68)
	groupList.ScrollBarThickness = 4
	groupList.CanvasSize = UDim2.new()
	groupList.AutomaticCanvasSize = Enum.AutomaticSize.Y
	groupList.Parent = palette
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 5)
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = groupList

	tileGrid = Instance.new("ScrollingFrame")
	tileGrid.BackgroundTransparency = 1
	tileGrid.BorderSizePixel = 0
	tileGrid.Position = UDim2.fromOffset(196, 54)
	tileGrid.Size = UDim2.new(1, -208, 1, -68)
	tileGrid.ScrollBarThickness = 6
	tileGrid.CanvasSize = UDim2.new()
	tileGrid.AutomaticCanvasSize = Enum.AutomaticSize.Y
	tileGrid.Parent = palette
	local gridLayout = Instance.new("UIGridLayout")
	gridLayout.CellSize = UDim2.fromOffset(TILE, TILE)
	gridLayout.CellPadding = UDim2.fromOffset(8, 8)
	gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
	gridLayout.Parent = tileGrid
end

function HotbarUI.init()
	local gui = Instance.new("ScreenGui")
	gui.Name = "FactoryUI"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = false

	local bar = Instance.new("Frame")
	bar.BackgroundTransparency = 1
	bar.AnchorPoint = Vector2.new(0.5, 1)
	bar.Position = UDim2.new(0.5, 0, 1, -14)
	bar.Size = UDim2.fromOffset(#slots * (SLOT + 6), SLOT + 14)
	bar.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = bar

	for i, entry in slots do
		local frame = tile(bar, entry, SLOT, SLOT + 14)
		frame.LayoutOrder = i
		local number = label(frame, tostring(i), 11)
		number.Size = UDim2.fromOffset(14, 14)
		number.Position = UDim2.fromOffset(2, 0)
		number.TextColor3 = DIM
		local press = Instance.new("TextButton")
		press.BackgroundTransparency = 1
		press.Text = ""
		press.Size = UDim2.fromScale(1, 1)
		press.ZIndex = 5
		press.Parent = frame
		press.Activated:Connect(function()
			HotbarUI.select(i)
		end)
		slotFrames[i] = frame
	end

	bagLabel = label(gui, "", 14)
	bagLabel.AnchorPoint = Vector2.new(0.5, 1)
	bagLabel.Position = UDim2.new(0.5, 0, 1, -(SLOT + 36))
	bagLabel.Size = UDim2.fromOffset(900, 20)
	bagLabel.TextStrokeTransparency = 0.5

	stateLabel = label(gui, "", 14)
	stateLabel.AnchorPoint = Vector2.new(1, 0)
	stateLabel.Position = UDim2.new(1, -12, 0, 8)
	stateLabel.Size = UDim2.fromOffset(260, 20)
	stateLabel.TextXAlignment = Enum.TextXAlignment.Right
	stateLabel.TextStrokeTransparency = 0.5

	local hint = label(
		gui,
		"좌클릭 부수기 · 우클릭 놓기 · R 돌리기 · 1~9 고르기 · E 목록 · F 줍기",
		14
	)
	hint.AnchorPoint = Vector2.new(0.5, 0)
	hint.Position = UDim2.new(0.5, 0, 0, 8)
	hint.Size = UDim2.fromOffset(700, 20)
	hint.TextStrokeTransparency = 0.5

	toast = label(gui, "", 15)
	toast.AnchorPoint = Vector2.new(0.5, 0)
	toast.Position = UDim2.new(0.5, 0, 0, 40)
	toast.Size = UDim2.fromOffset(680, 48)
	toast.BackgroundTransparency = 0.15
	toast.BackgroundColor3 = PANEL
	toast.Visible = false
	toast.ZIndex = 10
	round(toast, 8)

	buildPalette(gui)
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	redrawSelection()
	showBag({})
	Net.get("Bag").OnClientEvent:Connect(showBag)
	Net.get("State").OnClientEvent:Connect(showState)
	Net.get("Notify").OnClientEvent:Connect(HotbarUI.notify)
end

return HotbarUI
