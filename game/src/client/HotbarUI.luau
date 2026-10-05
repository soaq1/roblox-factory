-- The ten quick slots (keys 1 to 9, then 0), the palette of things to place, and the bag and coin
-- read-outs. The selected slot is what is in the player's hand: left click uses it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local HotbarUI = {}

local SLOT = 66
local SLOTS = 10
local TILE = 96

local slots: { string } = table.create(SLOTS, "") -- "" is an empty slot
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
local selectListeners: { () -> () } = {}

-- Runs `run` whenever what is in the hand changes: another slot, or the slot's contents.
function HotbarUI.onSelect(run: () -> ())
	table.insert(selectListeners, run)
end

local function handChanged()
	Net.get("Hold"):FireServer(slots[selected])
	for _, run in selectListeners do
		task.spawn(run)
	end
end

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

-- In survival mode each slot shows how many of its thing the bag can supply, and is dimmed when
-- there are none. In creative mode everything is free, so nothing is shown.
local function redrawCounts()
	local survival = HotbarUI.state.mode == "survival"
	for i, frame in slotFrames do
		local count = frame:FindFirstChild("Count") :: TextLabel
		local dim = frame:FindFirstChild("Dim") :: Frame
		if survival and slots[i] ~= "" then
			local held = ScreenLogic.held(Defs, UIKit.Stock, HotbarUI.bag, slots[i])
			count.Text = UIKit.number(held)
			count.Visible = true
			dim.Visible = held < 1
		else
			count.Visible = false
			dim.Visible = false
		end
	end
end

local function redrawSlot(i: number)
	local frame = slotFrames[i]
	UIKit.picture(frame:FindFirstChild("Picture") :: Frame, slots[i])
	local name = frame:FindFirstChild("Name") :: TextLabel
	name.Text = if slots[i] == "" then "" else Defs.name(slots[i])
	redrawCounts()
	if i == selected then
		handChanged()
	end
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

-- Which of the slots is selected.
function HotbarUI.selectedIndex(): number
	return selected
end

function HotbarUI.select(index: number)
	if index >= 1 and index <= #slots and index ~= selected then
		selected = index
		redrawSelection()
		handChanged()
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

-- In survival mode the bar follows the bag the way an inventory would: a slot whose thing has run
-- out empties, and something newly gained takes the first empty slot.
local function follow()
	if HotbarUI.state.mode ~= "survival" then
		return
	end
	local onBar: { [string]: boolean } = {}
	for i, entry in slots do
		if entry ~= "" and ScreenLogic.held(Defs, UIKit.Stock, HotbarUI.bag, entry) < 1 then
			slots[i] = ""
			redrawSlot(i)
		end
		onBar[slots[i]] = true
	end
	for _, held in ScreenLogic.sorted(Defs, UIKit.Stock, HotbarUI.bag) do
		local forms = ScreenLogic.forms(Defs, UIKit.Stock, held.key)
		local entry = forms.place or forms.drop
		if entry and not onBar[entry] and not (forms.drop and onBar[forms.drop]) then
			local free = table.find(slots, "")
			if not free then
				return
			end
			slots[free] = entry
			onBar[entry] = true
			redrawSlot(free)
		end
	end
end

local function changed()
	follow()
	redrawCounts()
	for _, run in listeners do
		task.spawn(run)
	end
end

local function showBag(bag: { [string]: number })
	HotbarUI.bag = if type(bag) == "table" then bag else {}
	local kinds, total = ScreenLogic.totals(HotbarUI.bag)
	bagLabel.Text = if kinds > 0
		then "가방 " .. kinds .. "종 · " .. UIKit.number(total) .. "개 · E로 열기"
		else "가방 비어 있음 · E로 열기"
	changed()
end

local function showState(state)
	if type(state) ~= "table" then
		return
	end
	HotbarUI.state = {
		mode = if state.mode == "survival" then "survival" else "creative",
		coins = if type(state.coins) == "number" then state.coins else 0,
		tiers = if type(state.tiers) == "table" then state.tiers else {},
	}
	stateLabel.Text = (if HotbarUI.state.mode == "survival" then "생존" else "크리에이티브")
		.. " · "
		.. UIKit.number(HotbarUI.state.coins)
		.. "코인"
	changed()
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
		nil,
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

local function buildSlot(bar: Frame, i: number, entry: string)
	local frame = UIKit.tile(bar, entry, SLOT, SLOT + 14)
	frame.LayoutOrder = i
	local number = UIKit.label(frame, tostring(i % 10), 11)
	number.Size = UDim2.fromOffset(14, 14)
	number.Position = UDim2.fromOffset(2, 0)
	number.TextColor3 = UIKit.DIM

	-- A veil over the slot when the bag has none of it. It sits above the picture and under the
	-- count and the click cover.
	local dim = Instance.new("Frame")
	dim.Name = "Dim"
	dim.Size = UDim2.fromScale(1, 1)
	dim.BackgroundColor3 = UIKit.BACK
	dim.BackgroundTransparency = 0.4
	dim.BorderSizePixel = 0
	dim.ZIndex = 3
	dim.Visible = false
	dim.Parent = frame
	UIKit.round(dim, 8)

	local count = UIKit.label(frame, "", 12)
	count.Name = "Count"
	count.AnchorPoint = Vector2.new(1, 0)
	count.Position = UDim2.new(1, -4, 0, 2)
	count.Size = UDim2.fromOffset(40, 14)
	count.TextXAlignment = Enum.TextXAlignment.Right
	count.TextWrapped = false
	count.TextStrokeTransparency = 0.4
	count.ZIndex = 4
	count.Visible = false

	UIKit.cover(frame, function()
		HotbarUI.select(i)
	end)
	slotFrames[i] = frame
end

function HotbarUI.init()
	local gui = Screens.gui()
	-- Windows are made after the hotbar and must cover it where they overlap. That needs the
	-- layering to go by parent first rather than by one number across the whole screen.
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

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
		buildSlot(bar, i, entry)
	end

	-- One short line: what the bag holds in full is on the bag screen.
	bagLabel = UIKit.label(gui, "", 14)
	bagLabel.AnchorPoint = Vector2.new(0.5, 1)
	bagLabel.Position = UDim2.new(0.5, 0, 1, -(SLOT + 36))
	bagLabel.Size = UDim2.fromOffset(420, 20)
	bagLabel.TextWrapped = false
	bagLabel.TextStrokeTransparency = 0.5

	stateLabel = UIKit.label(gui, "", 14)
	stateLabel.AnchorPoint = Vector2.new(1, 0)
	stateLabel.Position = UDim2.new(1, -12, 0, 8)
	stateLabel.Size = UDim2.fromOffset(260, 20)
	stateLabel.TextXAlignment = Enum.TextXAlignment.Right
	stateLabel.TextStrokeTransparency = 0.5

	local hint = UIKit.label(
		gui,
		"1~0 고르기 · 좌클릭 쓰기 · Q 떨구기 · R 돌리기 · F 줍기·상호작용 · E 가방 · Shift 달리기 · C 조합 · T 거래 · V 섬 구경",
		14
	)
	hint.Name = "Hint"
	hint.AnchorPoint = Vector2.new(0.5, 0)
	hint.Position = UDim2.new(0.5, 0, 0, 8)
	hint.Size = UDim2.fromOffset(900, 20)
	hint.TextWrapped = false
	hint.TextStrokeTransparency = 0.5

	buildPalette()
	-- E is the inventory, as in Minecraft: what is carried in survival, everything in creative.
	Screens.onKey(Enum.KeyCode.E, function()
		if Screens.isOpen("bag") or Screens.isOpen("palette") then
			Screens.closeAll()
		else
			Screens.open(if HotbarUI.state.mode == "creative" then "palette" else "bag")
		end
	end)
	redrawSelection()
	handChanged()
	showBag({})
	Net.get("Bag").OnClientEvent:Connect(showBag)
	Net.get("State").OnClientEvent:Connect(showState)
	Net.get("Notify").OnClientEvent:Connect(UIKit.toast)
end

return HotbarUI
