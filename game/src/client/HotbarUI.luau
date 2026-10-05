-- The ten quick slots (keys 1 to 9, then 0), the palette of things to place, and the bag and coin
-- read-outs. The selected slot is what is in the player's hand: left click uses it.
-- The bar is the player's own arrangement: it is saved, restored on the next visit, and only ever
-- changed by the player, except that something newly gained takes an empty slot.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local ToolLogic = require(Shared:WaitForChild("ToolLogic"))
local Screens = require(script.Parent.Screens)
local Settings = require(script.Parent.Settings)
local UIKit = require(script.Parent.UIKit)

local HotbarUI = {}

local SLOT = 66
local SLOTS = 10
local GAP = 6
local BAR_W = SLOTS * (SLOT + GAP)
local BAR_H = SLOT + 14
local TILE = 96
local PHONE_SIDE_ROOM = 130 -- pixels kept free at each end for the thumbstick and the jump button
local GAIN_SECONDS = 2.2 -- how long a "+2 통나무" line stays
local GAIN_MERGE = 1 -- gains of one kind this close together are shown as one number
local GAIN_LINES = 5
local PREFS_WAIT = 6 -- seconds to wait for the saved bar before carrying on without it

local slots: { string } = table.create(SLOTS, "") -- "" is an empty slot
local selected = 1
local slotFrames: { Frame } = {}
local dock: Frame
local arrangePanel: Frame
local gainFrame: Frame
local hint: TextLabel
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

local barReady = false -- the saved bar has been put back (or found to be absent)
local bagArrived = false
local stateArrived = false
local askedForBar = false
local seen: { [string]: boolean }? = nil -- the kinds the bag held at the last look
local arranging: number? = nil -- the slot being moved, while the player rearranges
local savePending = false
local keyboardLast = true

type Gain = { label: TextLabel, n: number, at: number, token: number }
local gainLines: { [string]: Gain } = {}
local gainOrder = 0

local function isTool(key: string): boolean
	return (ToolLogic.parse(key)) ~= nil
end

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

-- Saves the bar a moment from now, so several slots changing together are sent once. Nothing is
-- saved before the stored bar has been put back, or it would be overwritten with an empty one.
local function saveSoon()
	if not barReady or savePending then
		return
	end
	savePending = true
	task.defer(function()
		savePending = false
		Settings.saveBar(slots)
	end)
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
-- there are none: the slot keeps its place for when there are some again. In creative mode
-- everything is free, so nothing is shown.
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
		if i == arranging then
			stroke.Color = UIKit.GOOD
			stroke.Thickness = 3
		else
			stroke.Color = if i == selected then UIKit.PICK else UIKit.LINE
			stroke.Thickness = if i == selected then 3 else 1
		end
	end
end

function HotbarUI.selected(): string
	return slots[selected]
end

-- Which of the slots is selected.
function HotbarUI.selectedIndex(): number
	return selected
end

-- The ten entries of the bar, in order. "" is an empty slot.
function HotbarUI.slots(): { string }
	return table.clone(slots)
end

local function setSlot(i: number, entry: string)
	slots[i] = entry
	redrawSlot(i)
	saveSoon()
end

-- Rearranging. A long press or a right click on a slot picks it up; the next slot pressed (or its
-- number key) trades places with it. A small panel offers to empty the slot or to leave it be.
local function endArrange()
	arranging = nil
	arrangePanel.Visible = false
	gainFrame.Visible = true
	redrawSelection()
end

local function beginArrange(i: number)
	arranging = i
	arrangePanel.Visible = true
	gainFrame.Visible = false
	redrawSelection()
end

local function swap(a: number, b: number)
	local after = ScreenLogic.swapSlots(slots, a, b)
	for i = 1, SLOTS do
		slots[i] = after[i]
	end
	redrawSlot(a)
	redrawSlot(b)
	saveSoon()
end

function HotbarUI.select(index: number)
	if index < 1 or index > #slots then
		return
	end
	local moving = arranging
	if moving then
		endArrange()
		if moving ~= index then
			swap(moving, index)
		end
		return
	end
	if index ~= selected then
		selected = index
		redrawSelection()
		handChanged()
	end
end

-- Puts a palette entry into the selected slot.
function HotbarUI.assign(entry: string)
	if Defs.isEntry(entry) then
		setSlot(selected, entry)
	end
end

function HotbarUI.notify(text: string)
	UIKit.toast(text)
end

-- E: the inventory, as in Minecraft. What is carried in survival, everything in creative.
function HotbarUI.openInventory()
	if Screens.isOpen("bag") or Screens.isOpen("palette") then
		Screens.closeAll()
	else
		Screens.open(if HotbarUI.state.mode == "creative" then "palette" else "bag")
	end
end

local function keySet(bag: { [string]: number }): { [string]: boolean }
	local set = {}
	for key in bag do
		set[key] = true
	end
	return set
end

-- Something newly gained takes an empty slot; nothing else on the bar is touched. A slot whose
-- thing has run out keeps it. A bar with nothing on it at all (a first visit, or coming over from
-- creative mode) takes whatever is carried, tools first.
local function follow()
	if not (barReady and bagArrived and stateArrived) then
		return
	end
	local fresh = if seen then ScreenLogic.newKinds(seen, HotbarUI.bag) else {}
	seen = keySet(HotbarUI.bag)
	if HotbarUI.state.mode ~= "survival" then
		return
	end
	local bare = true
	for _, entry in slots do
		bare = bare and entry == ""
	end
	if bare then
		fresh = ScreenLogic.newKinds({}, HotbarUI.bag)
	end
	if #fresh == 0 then
		return
	end
	local after, changed = ScreenLogic.fillSlots(Defs, UIKit.Stock, slots, fresh, isTool)
	if not changed then
		return
	end
	for i = 1, SLOTS do
		if after[i] ~= slots[i] then
			slots[i] = after[i]
			redrawSlot(i)
		end
	end
	saveSoon()
end

-- Puts the stored bar back. Called once, when the server's copy arrives after the island is ready.
local function restore(saved: { any })
	if barReady then
		return
	end
	if #saved >= SLOTS then
		for i = 1, SLOTS do
			local entry = saved[i]
			slots[i] = if type(entry) == "string" and Defs.isEntry(entry) then entry else ""
		end
	end
	barReady = true
	for i = 1, SLOTS do
		redrawSlot(i)
	end
	follow()
	redrawCounts()
end

local function changed()
	follow()
	redrawCounts()
	for _, run in listeners do
		task.spawn(run)
	end
end

local function drawBagLabel()
	local kinds, total = ScreenLogic.totals(HotbarUI.bag)
	bagLabel.Text = if kinds > 0
		then "가방 " .. kinds .. "종 · " .. UIKit.number(total) .. "개"
		else "가방 비어 있음"
end

-- "+2 통나무" above the bar for a moment. Gains of one kind close together are shown as one number.
local function showGain(key: string, n: number)
	local now = os.clock()
	local line = gainLines[key]
	local total =
		ScreenLogic.mergeGain(if line then line.n else nil, if line then line.at else nil, n, now, GAIN_MERGE)
	if not line then
		local label = UIKit.label(gainFrame, "", 14)
		label.Size = UDim2.new(1, 0, 0, 20)
		label.TextWrapped = false
		label.TextColor3 = UIKit.GOOD
		label.TextStrokeTransparency = 0.4
		line = { label = label, n = 0, at = now, token = 0 }
		gainLines[key] = line
	end
	gainOrder += 1
	line.n = total
	line.at = now
	line.token += 1
	line.label.LayoutOrder = gainOrder
	line.label.Visible = true
	line.label.Text = "+" .. UIKit.number(total) .. " " .. UIKit.Stock.name(key)
	local token = line.token
	task.delay(GAIN_SECONDS, function()
		if gainLines[key] == line and line.token == token then
			gainLines[key] = nil
			line.label:Destroy()
		end
	end)
	-- Keep only the newest few on screen.
	local shown = {}
	for _, other in gainLines do
		table.insert(shown, other)
	end
	if #shown > GAIN_LINES then
		table.sort(shown, function(a, b)
			return a.label.LayoutOrder < b.label.LayoutOrder
		end)
		for i = 1, #shown - GAIN_LINES do
			shown[i].label.Visible = false
		end
	end
end

local function showBag(bag: { [string]: number })
	local before = HotbarUI.bag
	HotbarUI.bag = if type(bag) == "table" then bag else {}
	-- What was already carried on arrival is not a gain.
	if bagArrived then
		for _, gain in ScreenLogic.gains(before, HotbarUI.bag) do
			if UIKit.Stock.isKey(gain.key) then
				showGain(gain.key, gain.n)
			end
		end
	end
	bagArrived = true
	drawBagLabel()
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
	stateArrived = true
	-- The first state arrives once the island has finished loading, which is when the stored bar
	-- is sure to be on the server. Ask for it now; an answer from before this may have come too
	-- early to hold it.
	if not askedForBar then
		askedForBar = true
		Net.get("Prefs"):FireServer("load")
		task.delay(PREFS_WAIT, function()
			restore({})
		end)
	end
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
		end, entry)
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
			item.Size = UDim2.new(1, -6, 0, 32)
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
	-- Laid out smaller on a phone, where the window is then drawn larger to fill the screen.
	local compact = UIKit.compact()
	local side = if compact then 140 else 170
	local _, body = UIKit.window(
		"palette",
		"놓을 것 고르기 · 고르면 지금 선택된 칸에 들어갑니다",
		if compact then 640 else 760,
		if compact then 300 else 470,
		nil,
		function()
			showTab(currentTab)
		end
	)

	local x = 0
	for _, tab in Defs.Tabs do
		local item = UIKit.button(body, tab, 15)
		item.AutoButtonColor = false
		item.Size = UDim2.fromOffset(90, 32)
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
	groupList.Size = UDim2.new(0, side, 1, -40)

	tileGrid = UIKit.scroller(body, Vector2.new(TILE, TILE), 8)
	tileGrid.Position = UDim2.fromOffset(side + 12, 40)
	tileGrid.Size = UDim2.new(1, -(side + 12), 1, -40)
end

local function buildSlot(bar: Frame, i: number, entry: string)
	local frame = UIKit.tile(bar, entry, SLOT, BAR_H)
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

	-- A press selects the slot. A long press or a right click picks it up to be moved.
	local wasHold: () -> boolean
	local press = UIKit.cover(frame, function()
		if not wasHold() then
			HotbarUI.select(i)
		end
	end)
	wasHold = UIKit.hold(press, function()
		beginArrange(i)
	end)
	slotFrames[i] = frame
end

local function buildArrangePanel()
	arrangePanel = Instance.new("Frame")
	arrangePanel.Name = "Arrange"
	arrangePanel.AnchorPoint = Vector2.new(0.5, 1)
	arrangePanel.Position = UDim2.new(0.5, 0, 0, -30)
	arrangePanel.Size = UDim2.fromOffset(470, 44)
	arrangePanel.BackgroundColor3 = UIKit.BACK
	arrangePanel.BorderSizePixel = 0
	arrangePanel.Visible = false
	arrangePanel.Parent = dock
	UIKit.round(arrangePanel, 8)
	UIKit.stroke(arrangePanel, UIKit.GOOD)

	local text = UIKit.label(arrangePanel, "자리를 바꿀 칸을 누르세요", 13)
	text.TextXAlignment = Enum.TextXAlignment.Left
	text.TextWrapped = false
	text.Position = UDim2.fromOffset(12, 0)
	text.Size = UDim2.new(1, -200, 1, 0)

	local empty = UIKit.button(arrangePanel, "칸 비우기", 13)
	empty.AnchorPoint = Vector2.new(1, 0.5)
	empty.Position = UDim2.new(1, -86, 0.5, 0)
	empty.Size = UDim2.fromOffset(92, 34)
	empty.Activated:Connect(function()
		local moving = arranging
		endArrange()
		if moving then
			setSlot(moving, "")
		end
	end)

	local cancel = UIKit.button(arrangePanel, "그만", 13)
	cancel.AnchorPoint = Vector2.new(1, 0.5)
	cancel.Position = UDim2.new(1, -8, 0.5, 0)
	cancel.Size = UDim2.fromOffset(72, 34)
	cancel.Activated:Connect(endArrange)
end

-- Is this kind of input a keyboard-and-mouse player's?
local function isDeskInput(kind: Enum.UserInputType): boolean
	return kind == Enum.UserInputType.Keyboard
		or kind == Enum.UserInputType.MouseButton1
		or kind == Enum.UserInputType.MouseButton2
		or kind == Enum.UserInputType.MouseButton3
		or kind == Enum.UserInputType.MouseMovement
		or kind == Enum.UserInputType.MouseWheel
end

-- The bar keeps its size in pixels and shrinks only where the screen is too narrow for it. On a
-- phone a window takes the whole screen, so the bar steps aside while one is open. The line of
-- keys is only for someone at a keyboard.
local function fitToScreen(barFit: UIScale)
	local view = UIKit.viewport()
	local compact = UIKit.compact()
	local sideRoom = if compact and UIKit.touch() then PHONE_SIDE_ROOM else 8
	barFit.Scale = ScreenLogic.barScale(view.X, BAR_W, sideRoom)
	dock.Visible = not (compact and Screens.anyOpen())
	hint.Visible = keyboardLast and not compact
	-- Where the screen is too narrow for the coin read-out to sit beside the menu buttons, it
	-- goes under them.
	-- Roblox draws its own player list in the top right corner, so this sits at the bottom left.
	stateLabel.Position = UDim2.new(0, 14, 1, -16)
end

function HotbarUI.init()
	local gui = Screens.gui()

	-- Everything at the bottom of the screen sits in one frame, so it scales and hides together.
	dock = Instance.new("Frame")
	dock.Name = "Dock"
	dock.BackgroundTransparency = 1
	dock.AnchorPoint = Vector2.new(0.5, 1)
	dock.Position = UDim2.new(0.5, 0, 1, -14)
	dock.Size = UDim2.fromOffset(BAR_W, BAR_H)
	dock.Parent = gui
	local barFit = Instance.new("UIScale")
	barFit.Parent = dock

	local bar = Instance.new("Frame")
	bar.Name = "Bar"
	bar.BackgroundTransparency = 1
	bar.Size = UDim2.fromScale(1, 1)
	bar.Parent = dock
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.Padding = UDim.new(0, GAP)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = bar

	for i, entry in slots do
		buildSlot(bar, i, entry)
	end

	-- One short line: what the bag holds in full is on the bag screen.
	bagLabel = UIKit.label(dock, "", 14)
	bagLabel.AnchorPoint = Vector2.new(0.5, 1)
	bagLabel.Position = UDim2.new(0.5, 0, 0, -6)
	bagLabel.Size = UDim2.fromOffset(420, 20)
	bagLabel.TextWrapped = false
	bagLabel.TextStrokeTransparency = 0.5

	gainFrame = Instance.new("Frame")
	gainFrame.Name = "Gains"
	gainFrame.BackgroundTransparency = 1
	gainFrame.AnchorPoint = Vector2.new(0.5, 1)
	gainFrame.Position = UDim2.new(0.5, 0, 0, -30)
	gainFrame.Size = UDim2.fromOffset(360, GAIN_LINES * 22)
	gainFrame.Parent = dock
	local gainLayout = Instance.new("UIListLayout")
	gainLayout.VerticalAlignment = Enum.VerticalAlignment.Bottom
	gainLayout.Padding = UDim.new(0, 2)
	gainLayout.SortOrder = Enum.SortOrder.LayoutOrder
	gainLayout.Parent = gainFrame

	buildArrangePanel()

	stateLabel = UIKit.label(gui, "", 14)
	stateLabel.AnchorPoint = Vector2.new(0, 1)
	stateLabel.Position = UDim2.new(0, 14, 1, -16)
	stateLabel.Size = UDim2.fromOffset(260, 22)
	stateLabel.TextSize = 16
	stateLabel.TextXAlignment = Enum.TextXAlignment.Left
	stateLabel.TextWrapped = false
	stateLabel.TextStrokeTransparency = 0.5

	-- Under the row of menu buttons. Shown only to someone using a keyboard.
	hint = UIKit.label(
		gui,
		"1~0 고르기 · 좌클릭 쓰기 · Q 떨구기 · R 돌리기 · F 줍기·상호작용 · E 가방 · Shift 달리기 · C 조합 · T 거래 · V 섬 구경",
		13
	)
	hint.Name = "Hint"
	hint.AnchorPoint = Vector2.new(0.5, 0)
	hint.Position = UDim2.new(0.5, 0, 0, 54)
	hint.Size = UDim2.new(1, -24, 0, 20)
	hint.TextWrapped = false
	hint.TextTruncate = Enum.TextTruncate.AtEnd
	hint.TextStrokeTransparency = 0.5
	local hintWidest = Instance.new("UISizeConstraint")
	hintWidest.MaxSize = Vector2.new(900, 20)
	hintWidest.Parent = hint

	buildPalette()
	Screens.onKey(Enum.KeyCode.E, HotbarUI.openInventory)
	-- In creative E is the full list, so the bag keeps a key of its own.
	Screens.onKey(Enum.KeyCode.B, function()
		Screens.toggle("bag")
	end)

	keyboardLast = isDeskInput(UserInputService:GetLastInputType())
	UserInputService.LastInputTypeChanged:Connect(function(kind)
		-- Other kinds (focus changes, text input) say nothing about what the player is holding.
		if isDeskInput(kind) then
			keyboardLast = true
		elseif kind == Enum.UserInputType.Touch or string.find(kind.Name, "Gamepad") then
			keyboardLast = false
		end
		hint.Visible = keyboardLast and not UIKit.compact()
	end)
	local function refit()
		fitToScreen(barFit)
	end
	gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(refit)
	Screens.onChange(refit)
	refit()

	redrawSelection()
	handChanged()
	drawBagLabel()
	redrawCounts()
	Net.get("Bag").OnClientEvent:Connect(showBag)
	Net.get("State").OnClientEvent:Connect(showState)
	Net.get("Notify").OnClientEvent:Connect(UIKit.toast)
	-- The stored bar, once it has been asked for after the island was ready (see showState).
	Net.get("Prefs").OnClientEvent:Connect(function(saved)
		if askedForBar and type(saved) == "table" then
			restore(if type(saved.bar) == "table" then saved.bar else {})
		end
	end)
end

return HotbarUI
