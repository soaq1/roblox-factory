-- The crafting screen (C): what can be made by hand, where, and from what. Three tabs: crafting at
-- workbenches, working materials at a hand station, and raising a workbench's tier.
-- The first group on a tab lists whatever can be made right now, wherever it is made; a search
-- box finds a recipe by the name of what it makes.
-- The screen only shows and asks. Whether something is really made is decided by the server.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local CraftLogic = require(Shared:WaitForChild("CraftLogic"))
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local Recipes = require(Shared:WaitForChild("Recipes"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local CraftUI = {}

local player = Players.LocalPlayer
local Stock = UIKit.Stock
local ROW = 74

local NOW = "now" -- the name of the group of things that can be made right now
local SIDE = 190 -- width of the list of groups; narrower on a phone

type Row = { kind: string, index: number } -- kind is "craft" or "hand"; index is into that list

local hotbar
local groupList: ScrollingFrame
local rowList: ScrollingFrame
local nearLabel: TextLabel
local search: TextBox
local tabButtons: { [string]: TextButton } = {}
local groupButtons: { [string]: TextButton } = {}
local groupTotals: { [string]: number } = {}
local tab = "craft"
local group: string? = nil
local rows: { () -> () } = {} -- one refresh function per row on show
local benches: { [string]: number } = {}
local watching = 0
local openAt: string? = nil -- the group to show when the screen next opens
-- What the "can be made now" group is showing. A row stays once shown, greyed if it can no
-- longer be made, so that making something does not pull the list out from under the cursor.
local nowShown: { craft: { [number]: boolean }, hand: { [number]: boolean } } = { craft = {}, hand = {} }

-- The name of each kind of bench, and the machine that is that bench (for its picture).
local benchNames: { [string]: string } = { bag = "가방" }
local benchMachine: { [string]: string } = {}
for id, def in Defs.Machines do
	if def.behavior == "bench" then
		benchNames[def.bench] = def.name
		benchMachine[def.bench] = id
	end
end

local function hex(color: Color3): string
	return string.format(
		"#%02x%02x%02x",
		math.floor(color.R * 255),
		math.floor(color.G * 255),
		math.floor(color.B * 255)
	)
end

local function plain(text: string): string
	local out = string.gsub(text, "&", "&amp;")
	out = string.gsub(out, "<", "&lt;")
	out = string.gsub(out, ">", "&gt;")
	return out
end

local function tint(text: string, color: Color3): string
	return '<font color="' .. hex(color) .. '">' .. plain(text) .. "</font>"
end

-- "철판 3/2 · 철 막대 1/2", with what is short in red.
local function costText(bag: { [string]: number }, ins: { [string]: number }): string
	local keys = {}
	for key in ins do
		table.insert(keys, key)
	end
	table.sort(keys, function(a, b)
		return Stock.name(a) < Stock.name(b)
	end)
	local parts = {}
	for _, key in keys do
		local have = bag[key] or 0
		local text = Stock.name(key) .. " " .. UIKit.number(have) .. "/" .. UIKit.number(ins[key])
		table.insert(parts, tint(text, if have >= ins[key] then UIKit.TEXT else UIKit.BAD))
	end
	return table.concat(parts, tint(" · ", UIKit.DIM))
end

local function amounts(bag: { [string]: number }): string
	local parts = {}
	for key, n in bag do
		table.insert(parts, Stock.name(key) .. " " .. n)
	end
	table.sort(parts)
	return table.concat(parts, " · ")
end

-- Why something cannot be made, in words.
local function explain(reason: string?, detail: any): string
	if reason == "bench" then
		return (benchNames[detail] or tostring(detail)) .. " 가까이에서만 할 수 있습니다"
	elseif reason == "tier" then
		return "작업대 " .. tostring(detail) .. "단계가 필요합니다"
	elseif reason == "missing" then
		return Stock.name(detail) .. "이(가) 모자랍니다"
	elseif reason == "tool" then
		return Stock.name(detail) .. "이(가) 있어야 합니다"
	elseif reason == "fuel" then
		return "땔감이 모자랍니다"
	elseif reason == "full" then
		return "가방에 더 넣을 수 없습니다"
	elseif reason == "max" then
		return "이미 가장 높은 단계입니다"
	end
	return ""
end

-- Which benches on my own island are within reach, measured the same way the server does.
local function benchesNow(): { [string]: number }
	local seen = {}
	local island = Workspace:FindFirstChild("Island_" .. player.UserId)
	local folder = island and island:FindFirstChild("Machines")
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if folder and root and root:IsA("BasePart") then
		for _, model in folder:GetChildren() do
			local id = model:GetAttribute("Machine")
			local def = if type(id) == "string" then Defs.Machines[id] else nil
			local body = model:FindFirstChild("Body")
			if def and def.behavior == "bench" and body and body:IsA("BasePart") then
				-- The body is as tall as the machine; the server measures to the footprint's
				-- centre at the height of a cell's centre.
				local height = math.max(def.height, 1)
				local centre = body.Position - Vector3.new(0, height / 2 - Config.CELL / 2, 0)
				table.insert(seen, { kind = def.bench, distance = (centre - root.Position).Magnitude })
			end
		end
	end
	return ScreenLogic.benchesNear(seen, hotbar.state.tiers, Config.BENCH_RANGE)
end

local function sameBenches(a: { [string]: number }, b: { [string]: number }): boolean
	for kind, tier in a do
		if b[kind] ~= tier then
			return false
		end
	end
	for kind, tier in b do
		if a[kind] ~= tier then
			return false
		end
	end
	return true
end

-- A row: picture, title, a line or two of detail, and buttons on the right.
local function makeRow(order: number, picture: string, title: string): (TextLabel, Frame, TextLabel)
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(1, -10, 0, ROW)
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	frame.LayoutOrder = order
	frame.Parent = rowList
	UIKit.round(frame, 8)

	local art = Instance.new("Frame")
	art.BackgroundTransparency = 1
	art.Position = UDim2.fromOffset(8, 8)
	art.Size = UDim2.fromOffset(ROW - 16, ROW - 16)
	art.Parent = frame
	UIKit.picture(art, picture)
	-- Pressing the picture opens what is known about the thing: how it is made, what it goes into.
	UIKit.cover(art, function()
		UIKit.info(picture)
	end)

	local name = UIKit.label(frame, title, 14)
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.TextWrapped = false
	name.TextTruncate = Enum.TextTruncate.AtEnd
	name.Position = UDim2.fromOffset(ROW, 6)
	name.Size = UDim2.new(1, -(ROW + 186), 0, 20)

	local info = UIKit.label(frame, "", 12)
	info.RichText = true
	info.TextXAlignment = Enum.TextXAlignment.Left
	info.TextYAlignment = Enum.TextYAlignment.Top
	info.Position = UDim2.fromOffset(ROW, 28)
	info.Size = UDim2.new(1, -(ROW + 186), 0, ROW - 32)

	local actions = Instance.new("Frame")
	actions.BackgroundTransparency = 1
	actions.AnchorPoint = Vector2.new(1, 0.5)
	actions.Position = UDim2.new(1, -8, 0.5, 0)
	actions.Size = UDim2.fromOffset(172, 34)
	actions.Parent = frame
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	layout.Padding = UDim.new(0, 4)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = actions
	return info, actions, name
end

local function actionButton(
	actions: Frame,
	order: number,
	text: string,
	width: number,
	run: () -> ()
): TextButton
	local item = UIKit.button(actions, text, 13)
	item.BackgroundColor3 = UIKit.BACK
	item.Size = UDim2.fromOffset(width, 34)
	item.LayoutOrder = order
	item.Activated:Connect(run)
	return item
end

local function setEnabled(item: TextButton, enabled: boolean)
	item.Active = enabled
	item.AutoButtonColor = enabled
	item.TextTransparency = if enabled then 0 else 0.6
end

-- The 1 / 10 / as-many-as-possible buttons. `most` says how many can be made right now and
-- `send` asks the server for that many.
local function timesButtons(actions: Frame, most: () -> number, send: (times: number) -> ())
	local one = actionButton(actions, 1, "1", 40, function()
		if most() >= 1 then
			send(1)
		end
	end)
	local ten = actionButton(actions, 2, "10", 44, function()
		if most() >= 10 then
			send(10)
		end
	end)
	local all = actionButton(actions, 3, "최대", 78, function()
		local times = most()
		if times >= 1 then
			send(times)
		end
	end)
	return function()
		local times = most()
		setEnabled(one, times >= 1)
		setEnabled(ten, times >= 10)
		setEnabled(all, times >= 1)
		all.Text = if times >= 1 then "최대 " .. times else "최대"
	end
end

local function craftRow(order: number, index: number)
	local recipe = Recipes.craft[index]
	local title = Stock.name(recipe.out) .. (if recipe.n > 1 then " ×" .. recipe.n else "")
	if recipe.tier > 1 then
		title ..= " · " .. recipe.tier .. "단계"
	end
	local info, actions = makeRow(order, recipe.out, title)
	local function most(): number
		if CraftLogic.blocked(hotbar.bag, recipe, benches, 1) then
			return 0
		end
		return ScreenLogic.maxTimes(hotbar.bag, recipe.ins, CraftLogic.MAX_TIMES)
	end
	local redrawButtons = timesButtons(actions, most, function(times)
		Net.get("Craft"):FireServer(index, times)
	end)
	table.insert(rows, function()
		local reason, detail = CraftLogic.blocked(hotbar.bag, recipe, benches, 1)
		local text = costText(hotbar.bag, recipe.ins)
		-- A missing ingredient already shows in red; say the rest in words.
		if reason and reason ~= "missing" then
			text ..= "\n" .. tint(explain(reason, detail), UIKit.PICK)
		end
		info.Text = text
		redrawButtons()
	end)
end

local function handRow(order: number, index: number)
	local recipe = Recipes.hand[index]
	local outs = {}
	for key in recipe.outs do
		table.insert(outs, key)
	end
	table.sort(outs)
	local info, actions = makeRow(order, outs[1], amounts(recipe.outs))
	local function most(): number
		local times =
			ScreenLogic.maxHand(CraftLogic, hotbar.bag, recipe, benches, Recipes.fuel, CraftLogic.MAX_TIMES)
		if times < 1 then
			-- Heat left over from the last fire is known only to the server. If fuel is the
			-- only thing in the way, let one be tried and the server say.
			local _, reason = CraftLogic.hand(table.clone(hotbar.bag), recipe, benches, 1, Recipes.fuel, 0)
			if reason == "fuel" then
				return 1
			end
		end
		return times
	end
	local redrawButtons = timesButtons(actions, most, function(times)
		Net.get("Hand"):FireServer(index, times)
	end)
	table.insert(rows, function()
		local ok, reason, detail =
			CraftLogic.hand(table.clone(hotbar.bag), recipe, benches, 1, Recipes.fuel, 0)
		local text = costText(hotbar.bag, recipe.ins)
		local needs = {}
		if recipe.tool then
			local held = (hotbar.bag[recipe.tool] or 0) >= 1
			table.insert(
				needs,
				tint("도구: " .. Stock.name(recipe.tool), if held then UIKit.DIM else UIKit.BAD)
			)
		end
		if recipe.fuel then
			table.insert(needs, tint("땔감 필요", if reason == "fuel" then UIKit.BAD else UIKit.DIM))
		end
		if #needs > 0 then
			text ..= tint(" · ", UIKit.DIM) .. table.concat(needs, tint(" · ", UIKit.DIM))
		end
		if not ok and reason == "bench" then
			text ..= "\n" .. tint(explain(reason, detail), UIKit.PICK)
		end
		info.Text = text
		redrawButtons()
	end)
end

local function upgradeRow(order: number, kind: string)
	local info, actions, name = makeRow(order, benchMachine[kind] or "wb_basic", benchNames[kind] or kind)
	local function check(): (boolean, string?, any)
		return CraftLogic.upgrade(
			table.clone(hotbar.bag),
			table.clone(hotbar.state.tiers),
			benches,
			kind,
			Recipes.upgrades
		)
	end
	local raise = actionButton(actions, 1, "올리기", 78, function()
		if check() then
			Net.get("Upgrade"):FireServer(kind)
		end
	end)
	table.insert(rows, function()
		local tier = hotbar.state.tiers[kind] or 1
		name.Text = (benchNames[kind] or kind) .. " · 지금 " .. tier .. "단계"
		local ok, reason, detail = check()
		local cost = Recipes.upgrades[kind .. ":" .. (tier + 1)]
		local text = if cost
			then tint((tier + 1) .. "단계로: ", UIKit.DIM) .. costText(hotbar.bag, cost)
			else tint("가장 높은 단계입니다", UIKit.GOOD)
		if not ok and reason == "bench" then
			text ..= "\n" .. tint(explain(reason, detail), UIKit.PICK)
		end
		info.Text = text
		setEnabled(raise, ok)
		raise.Visible = cost ~= nil
	end)
end

local function refreshRows()
	for _, refresh in rows do
		refresh()
	end
end

local function setOf(list: { number }): { [number]: boolean }
	local set = {}
	for _, index in list do
		set[index] = true
	end
	return set
end

local function canCraftNow(): { [number]: boolean }
	return setOf(ScreenLogic.makeable(CraftLogic, Recipes.craft, hotbar.bag, benches))
end

local function canHandNow(): { [number]: boolean }
	return setOf(ScreenLogic.makeableHand(CraftLogic, Recipes.hand, hotbar.bag, benches, Recipes.fuel))
end

local function sortedIndexes(set: { [number]: boolean }): { number }
	local list = {}
	for index in set do
		table.insert(list, index)
	end
	table.sort(list)
	return list
end

-- The hand recipes of one station.
local function handOf(station: string): { number }
	for _, entry in ScreenLogic.groups(Recipes.hand, "station") do
		if entry.name == station then
			return entry.indexes
		end
	end
	return {}
end

-- Does a recipe's product match what is typed in the search box?
local function found(row: Row): boolean
	if row.kind == "craft" then
		return ScreenLogic.matches(Stock.name(Recipes.craft[row.index].out), search.Text)
	end
	for key in Recipes.hand[row.index].outs do
		if ScreenLogic.matches(Stock.name(key), search.Text) then
			return true
		end
	end
	return false
end

-- The rows to show: the group that is selected, or, while something is typed in the search box,
-- every recipe on this tab whose product matches.
local function wantedRows(): { Row }
	local list: { Row } = {}
	local function add(kind: string, indexes: { number })
		for _, index in indexes do
			table.insert(list, { kind = kind, index = index })
		end
	end
	local searching = not ScreenLogic.matches("", search.Text)
	if searching then
		if tab == "craft" then
			for index in Recipes.craft do
				add("craft", { index })
			end
		end
		for index in Recipes.hand do
			add("hand", { index })
		end
		local hits = {}
		for _, row in list do
			if found(row) then
				table.insert(hits, row)
			end
		end
		return hits
	end
	if group == NOW then
		if tab == "craft" then
			add("craft", sortedIndexes(nowShown.craft))
		end
		add("hand", sortedIndexes(nowShown.hand))
	elseif group and tab == "craft" then
		for _, entry in ScreenLogic.groups(Recipes.craft, "bench") do
			if entry.name == group then
				add("craft", entry.indexes)
			end
		end
		-- The very first things (planks from a log) are hand work that needs no station. They
		-- are shown with the bag recipes too.
		if group == "bag" then
			add("hand", handOf("bag"))
		end
	elseif group then
		add("hand", handOf(group))
	end
	return list
end

-- "기계 작업대  3/41": how many of a group can be made now, out of how many. Dimmed when the bench
-- is not in reach.
local function refreshGroups()
	local craftNow, handNow = canCraftNow(), canHandNow()
	for name, item in groupButtons do
		local near = name == NOW
			or name == "bag"
			or benches[name] ~= nil
			or (benches.all ~= nil and table.find(ScreenLogic.WORKBENCHES, name) ~= nil)
		item.TextColor3 = if near then UIKit.TEXT else UIKit.DIM
		item.BackgroundColor3 = if name == group then UIKit.LINE else UIKit.PANEL
		local can = 0
		if name == NOW then
			for _ in handNow do
				can += 1
			end
			if tab == "craft" then
				for _ in craftNow do
					can += 1
				end
			end
			item.Text = "지금 만들 수 있음  " .. can
		else
			if tab == "craft" then
				for index in craftNow do
					can += if Recipes.craft[index].bench == name then 1 else 0
				end
			else
				for index in handNow do
					can += if Recipes.hand[index].station == name then 1 else 0
				end
			end
			item.Text = (benchNames[name] or name) .. "  " .. can .. "/" .. (groupTotals[name] or 0)
		end
	end
	local near = {}
	for kind in benches do
		table.insert(near, benchNames[kind] or kind)
	end
	table.sort(near)
	nearLabel.Text = if #near > 0
		then "가까운 작업대: " .. table.concat(near, ", ")
		else "가까운 작업대 없음 · 작업대 "
			.. Config.BENCH_RANGE
			.. "스터드 안에서 쓸 수 있습니다"
end

-- Draws the rows for the selected group or the search. `keep` leaves the list scrolled where it is.
local function render(keep: boolean?)
	local at = rowList.CanvasPosition
	rows = {}
	UIKit.clear(rowList)
	for order, row in wantedRows() do
		if row.kind == "craft" then
			craftRow(order, row.index)
		else
			handRow(order, row.index)
		end
	end
	rowList.CanvasPosition = if keep then at else Vector2.zero
	refreshRows()
	refreshGroups()
end

local function showGroup(name: string)
	group = name
	if name == NOW then
		-- A fresh look: only what can be made at this moment.
		nowShown = { craft = canCraftNow(), hand = canHandNow() }
	end
	render()
end

local function showTab(name: string, first: string?)
	tab = name
	group = nil
	rows = {}
	groupButtons = {}
	groupTotals = {}
	UIKit.clear(groupList)
	UIKit.clear(rowList)
	for key, item in tabButtons do
		item.BackgroundColor3 = if key == name then UIKit.LINE else UIKit.PANEL
	end

	if name == "upgrade" then
		-- No groups and nothing to search: one row for each of the seven workbenches.
		groupList.Visible = false
		search.Visible = false
		rowList.Position = UDim2.fromOffset(0, 62)
		rowList.Size = UDim2.new(1, 0, 1, -62)
		for order, kind in ScreenLogic.WORKBENCHES do
			upgradeRow(order, kind)
		end
		refreshRows()
		refreshGroups()
		return
	end

	groupList.Visible = true
	search.Visible = true
	rowList.Position = UDim2.fromOffset(SIDE + 12, 62)
	rowList.Size = UDim2.new(1, -(SIDE + 12), 1, -62)
	local groups = if name == "craft"
		then ScreenLogic.groups(Recipes.craft, "bench")
		else ScreenLogic.groups(Recipes.hand, "station")
	local function groupButton(order: number, key: string)
		local item = UIKit.button(groupList, "", 13)
		item.AutoButtonColor = false
		item.TextTruncate = Enum.TextTruncate.AtEnd
		item.Size = UDim2.new(1, -6, 0, 34)
		item.LayoutOrder = order
		item.Activated:Connect(function()
			-- Choosing a group puts the search away, or the group would not be what is shown.
			search.Text = ""
			showGroup(key)
		end)
		groupButtons[key] = item
	end
	groupButton(0, NOW)
	local wanted = NOW
	for order, entry in groups do
		groupTotals[entry.name] = #entry.indexes
		groupButton(order, entry.name)
		if entry.name == first then
			wanted = entry.name
		end
	end
	showGroup(wanted)
end

-- While the screen is open, notice when the player walks into or out of reach of a bench.
local function watch()
	watching += 1
	local token = watching
	benches = benchesNow()
	showTab(tab, openAt)
	openAt = nil
	task.spawn(function()
		while token == watching and Screens.isOpen("craft") do
			task.wait(1)
			if token ~= watching then
				return
			end
			local now = benchesNow()
			if not sameBenches(now, benches) then
				benches = now
				refreshRows()
				refreshGroups()
			end
		end
	end)
end

-- The bag, the tiers or the benches in reach changed. The rows stay and show new numbers; the
-- "can be made now" group also takes in anything that has just become makeable.
local function update()
	benches = benchesNow()
	if group == NOW and tab ~= "upgrade" and ScreenLogic.matches("", search.Text) then
		local grew = false
		for index in canHandNow() do
			grew = grew or not nowShown.hand[index]
			nowShown.hand[index] = true
		end
		if tab == "craft" then
			for index in canCraftNow() do
				grew = grew or not nowShown.craft[index]
				nowShown.craft[index] = true
			end
		end
		if grew then
			render(true)
			return
		end
	end
	refreshRows()
	refreshGroups()
end

-- Opens the screen at one tab ("craft", "hand" or "upgrade") and one of its groups (a bench kind,
-- a hand station). With `query` given, the search box is filled in too, which narrows the list to
-- the recipes that make that thing.
function CraftUI.reveal(tabName: string, groupName: string?, query: string?)
	tab = tabName
	search.Text = ""
	if Screens.isOpen("craft") then
		benches = benchesNow()
		showTab(tab, groupName)
	else
		openAt = groupName
		Screens.open("craft")
	end
	if query and tab ~= "upgrade" then
		search.Text = query
	end
end

function CraftUI.init(hotbarUi)
	hotbar = hotbarUi
	-- Laid out smaller on a phone, where the window is then drawn larger to fill the screen.
	local compact = UIKit.compact()
	SIDE = if compact then 150 else 190
	local _, body = UIKit.window(
		"craft",
		"조합",
		if compact then 660 else 860,
		if compact then 310 else 520,
		Enum.KeyCode.C,
		watch,
		function()
			watching += 1
		end
	)

	local x = 0
	for _, entry in { { "craft", "조합" }, { "hand", "손 작업" }, { "upgrade", "작업대 단계" } } do
		local item = UIKit.button(body, entry[2], 15)
		item.AutoButtonColor = false
		item.Size = UDim2.fromOffset(110, 32)
		item.Position = UDim2.fromOffset(x, 0)
		item.Activated:Connect(function()
			showTab(entry[1])
		end)
		tabButtons[entry[1]] = item
		x += 116
	end

	search = UIKit.input(body, "만들 것 찾기", 14)
	search.AnchorPoint = Vector2.new(1, 0)
	search.Position = UDim2.fromScale(1, 0)
	search.Size = UDim2.fromOffset(if compact then 140 else 220, 32)
	search:GetPropertyChangedSignal("Text"):Connect(function()
		if Screens.isOpen("craft") and tab ~= "upgrade" then
			render()
		end
	end)

	nearLabel = UIKit.label(body, "", 12)
	nearLabel.TextColor3 = UIKit.DIM
	nearLabel.TextXAlignment = Enum.TextXAlignment.Left
	nearLabel.TextWrapped = false
	nearLabel.TextTruncate = Enum.TextTruncate.AtEnd
	nearLabel.Position = UDim2.fromOffset(0, 38)
	nearLabel.Size = UDim2.new(1, 0, 0, 18)

	groupList = UIKit.scroller(body, nil, 5)
	groupList.ScrollBarThickness = 4
	groupList.Position = UDim2.fromOffset(0, 62)
	groupList.Size = UDim2.new(0, SIDE, 1, -62)

	rowList = UIKit.scroller(body, nil, 6)
	rowList.Position = UDim2.fromOffset(SIDE + 12, 62)
	rowList.Size = UDim2.new(1, -(SIDE + 12), 1, -62)

	-- F on a workbench or a hand station opens this screen at what that one makes.
	Net.get("MachineInfo").OnClientEvent:Connect(function(message)
		if type(message) ~= "table" or message.kind ~= "bench" or type(message.info) ~= "table" then
			return
		end
		local kind = message.info.bench
		local onHand = kind == "hand_furnace" or kind == "campfire"
		CraftUI.reveal(if onHand then "hand" else "craft", if type(kind) == "string" then kind else nil)
	end)

	hotbar.onChange(function()
		if Screens.isOpen("craft") then
			update()
		end
	end)
end

return CraftUI
