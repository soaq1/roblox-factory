-- The nine quick slots, the palette of things to place, and the bag and coin read-outs.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local HotbarUI = {}

local SLOT = 70
local TILE = 96

local slots = table.clone(Defs.DefaultHotbar)
local selected = 1
local slotFrames: { Frame } = {}
local groupList: ScrollingFrame
local tileGrid: ScrollingFrame
local tabButtons: { [string]: TextButton } = {}
local currentTab = Defs.Tabs[1]
local bagLabel: TextLabel
local stateLabel: TextLabel

-- What the server last said the player holds and is.
HotbarUI.bag = {} :: { [string]: number }
HotbarUI.state =
	{ mode = "creative", coins = 0, tiers = {} } :: { mode: string, coins: number, tiers: { [string]: number } }
local listeners: { () -> () } = {}

-- Runs `run` whenever the bag or the state changes.
function HotbarUI.onChange(run: () -> ())
	table.insert(listeners, run)
end

-- Machines that are only a model for now get a small tag saying so.
local function tagIfModelOnly(frame: Frame, entry: string)
	local def = Defs.Machines[entry]
	if def and def.behavior == "decor" then
		local tag = UIKit.label(frame, "모양만", 10)
		tag.Size = UDim2.fromOffset(40, 14)
		tag.Position = UDim2.new(1, -43, 0, 3)
		tag.TextColor3 = UIKit.DIM
		tag.BackgroundTransparency = 0.2
		tag.BackgroundColor3 = UIKit.BACK
		UIKit.round(tag, 4)
	end
end

local function redrawSlot(i: number)
	local frame = slotFrames[i]
	UIKit.picture(frame:FindFirstChild("Picture") :: Frame, slots[i])
	local name = frame:FindFirstChild("Name") :: TextLabel
	name.Text = Defs.name(slots[i])
end

local function redrawSelection()
	for i, frame in slotFrames do
		local stroke = frame:FindFirstChildOfClass("UIStroke") :: UIStroke
		stroke.Color = if i == selected then UIKit.PICK else UIKit.LINE
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

-- Puts a palette entry into the selected slot.
function HotbarUI.assign(entry: string)
	if Defs.isEntry(entry) then
		slots[selected] = entry
		redrawSlot(selected)
	end
end

function HotbarUI.notify(text: string)
	UIKit.toast(text)
end

local function showBag(bag: { [string]: number })
	HotbarUI.bag = bag
	local parts = {}
	for id, count in bag do
		table.insert(parts, UIKit.Stock.name(id) .. " " .. count)
	end
	table.sort(parts)
	bagLabel.Text = if #parts > 0
		then "가방: " .. table.concat(parts, "  ·  ")
		else "가방: 비어 있음"
	for _, run in listeners do
		task.spawn(run)
	end
end

local function showState(state)
	HotbarUI.state = state
	stateLabel.Text = (if state.mode == "survival" then "생존" else "크리에이티브")
		.. " · "
		.. UIKit.number(state.coins)
		.. "코인"
	for _, run in listeners do
		task.spawn(run)
	end
end

-- Shows the entries of one group in the right-hand grid.
local function showGroup(index: number)
	UIKit.clear(tileGrid)
	tileGrid.CanvasPosition = Vector2.zero
	for order, entry in Defs.Palette[index].ids do
		local frame = UIKit.tile(tileGrid, entry, TILE, TILE)
		frame.LayoutOrder = order
		tagIfModelOnly(frame, entry)
		UIKit.cover(frame, function()
			HotbarUI.assign(entry)
			local def = Defs.Machines[entry]
			if def and def.note ~= "" then
				UIKit.toast(def.name .. ": " .. def.note)
			end
		end)
	end
	for _, child in groupList:GetChildren() do
		if child:IsA("TextButton") then
			child.BackgroundColor3 = if child.LayoutOrder == index then UIKit.LINE else UIKit.PANEL
		end
	end
end

-- Shows the groups of one tab in the left-hand list and opens the first of them.
local function showTab(tab: string)
	currentTab = tab
	UIKit.clear(groupList)
	local first: number? = nil
	for index, group in Defs.Palette do
		if group.tab == tab then
			first = first or index
			local item = UIKit.button(groupList, group.name .. "  " .. #group.ids, 13)
			item.AutoButtonColor = false
			item.Size = UDim2.new(1, -6, 0, 30)
			item.LayoutOrder = index
			item.Activated:Connect(function()
				showGroup(index)
			end)
		end
	end
	for name, item in tabButtons do
		item.BackgroundColor3 = if name == tab then UIKit.LINE else UIKit.PANEL
	end
	if first then
		showGroup(first)
	end
end

local function buildPalette()
	local _, body = UIKit.window(
		"palette",
		"놓을 것 고르기 · 고르면 지금 선택된 칸에 들어갑니다",
		760,
		470,
		Enum.KeyCode.E,
		function()
			showTab(currentTab)
		end
	)

	local x = 0
	for _, tab in Defs.Tabs do
		local item = UIKit.button(body, tab, 15)
		item.AutoButtonColor = false
		item.Size = UDim2.fromOffset(90, 30)
		item.Position = UDim2.fromOffset(x, 0)
		item.Activated:Connect(function()
			showTab(tab)
		end)
		tabButtons[tab] = item
		x += 96
	end

	groupList = UIKit.scroller(body, nil, 5)
	groupList.ScrollBarThickness = 4
	groupList.Position = UDim2.fromOffset(0, 40)
	groupList.Size = UDim2.new(0, 170, 1, -40)

	tileGrid = UIKit.scroller(body, Vector2.new(TILE, TILE), 8)
	tileGrid.Position = UDim2.fromOffset(182, 40)
	tileGrid.Size = UDim2.new(1, -182, 1, -40)
end

function HotbarUI.init()
	local gui = Screens.gui()

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
		local frame = UIKit.tile(bar, entry, SLOT, SLOT + 14)
		frame.LayoutOrder = i
		local number = UIKit.label(frame, tostring(i), 11)
		number.Size = UDim2.fromOffset(14, 14)
		number.Position = UDim2.fromOffset(2, 0)
		number.TextColor3 = UIKit.DIM
		UIKit.cover(frame, function()
			HotbarUI.select(i)
		end)
		slotFrames[i] = frame
	end

	bagLabel = UIKit.label(gui, "", 14)
	bagLabel.AnchorPoint = Vector2.new(0.5, 1)
	bagLabel.Position = UDim2.new(0.5, 0, 1, -(SLOT + 36))
	bagLabel.Size = UDim2.fromOffset(900, 20)
	bagLabel.TextStrokeTransparency = 0.5

	stateLabel = UIKit.label(gui, "", 14)
	stateLabel.AnchorPoint = Vector2.new(1, 0)
	stateLabel.Position = UDim2.new(1, -12, 0, 8)
	stateLabel.Size = UDim2.fromOffset(260, 20)
	stateLabel.TextXAlignment = Enum.TextXAlignment.Right
	stateLabel.TextStrokeTransparency = 0.5

	local hint = UIKit.label(
		gui,
		"좌클릭 부수기 · 우클릭 놓기 · R 돌리기 · 1~9 고르기 · E 목록 · F 줍기",
		14
	)
	hint.Name = "Hint"
	hint.AnchorPoint = Vector2.new(0.5, 0)
	hint.Position = UDim2.new(0.5, 0, 0, 8)
	hint.Size = UDim2.fromOffset(700, 20)
	hint.TextStrokeTransparency = 0.5

	buildPalette()
	redrawSelection()
	showBag({})
	Net.get("Bag").OnClientEvent:Connect(showBag)
	Net.get("State").OnClientEvent:Connect(showState)
	Net.get("Notify").OnClientEvent:Connect(UIKit.toast)
end

return HotbarUI
