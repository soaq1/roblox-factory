-- The crafting screen (C): what can be made by hand, where, and from what. Three tabs: crafting at
-- workbenches, working materials at a hand station, and raising a workbench's tier.
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

local hotbar
local groupList: ScrollingFrame
local rowList: ScrollingFrame
local nearLabel: TextLabel
local tabButtons: { [string]: TextButton } = {}
local groupButtons: { [string]: TextButton } = {}
local tab = "craft"
local group: string? = nil
local rows: { () -> () } = {} -- one refresh function per row on show
local benches: { [string]: number } = {}
local watching = 0

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
	actions.Size = UDim2.fromOffset(172, 30)
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
	item.Size = UDim2.fromOffset(width, 30)
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

-- "기계 작업대 2단계", dimmed when it is not in reach.
local function refreshGroups()
	for name, item in groupButtons do
		local near = name == "bag"
			or benches[name] ~= nil
			or (benches.all ~= nil and table.find(ScreenLogic.WORKBENCHES, name) ~= nil)
		item.TextColor3 = if near then UIKit.TEXT else UIKit.DIM
		item.BackgroundColor3 = if name == group then UIKit.LINE else UIKit.PANEL
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

local function showGroup(name: string, indexes: { number })
	group = name
	rows = {}
	UIKit.clear(rowList)
	rowList.CanvasPosition = Vector2.zero
	for order, index in indexes do
		if tab == "craft" then
			craftRow(order, index)
		else
			handRow(order, index)
		end
	end
	-- The very first things (planks from a log) are hand work that needs no station. They are
	-- shown with the bag recipes too, so a new player finds them on the screen that opens.
	if tab == "craft" and name == "bag" then
		for _, entry in ScreenLogic.groups(Recipes.hand, "station") do
			if entry.name == "bag" then
				for order, index in entry.indexes do
					handRow(#indexes + order, index)
				end
			end
		end
	end
	refreshRows()
	refreshGroups()
end

local function showTab(name: string)
	tab = name
	group = nil
	rows = {}
	groupButtons = {}
	UIKit.clear(groupList)
	UIKit.clear(rowList)
	for key, item in tabButtons do
		item.BackgroundColor3 = if key == name then UIKit.LINE else UIKit.PANEL
	end

	if name == "upgrade" then
		-- No groups: one row for each of the seven workbenches.
		groupList.Visible = false
		rowList.Position = UDim2.fromOffset(0, 64)
		rowList.Size = UDim2.new(1, 0, 1, -64)
		for order, kind in ScreenLogic.WORKBENCHES do
			upgradeRow(order, kind)
		end
		refreshRows()
		refreshGroups()
		return
	end

	groupList.Visible = true
	rowList.Position = UDim2.fromOffset(202, 64)
	rowList.Size = UDim2.new(1, -202, 1, -64)
	local groups = if name == "craft"
		then ScreenLogic.groups(Recipes.craft, "bench")
		else ScreenLogic.groups(Recipes.hand, "station")
	for order, entry in groups do
		local item =
			UIKit.button(groupList, (benchNames[entry.name] or entry.name) .. "  " .. #entry.indexes, 13)
		item.AutoButtonColor = false
		item.Size = UDim2.new(1, -6, 0, 30)
		item.LayoutOrder = order
		item.Activated:Connect(function()
			showGroup(entry.name, entry.indexes)
		end)
		groupButtons[entry.name] = item
	end
	if groups[1] then
		showGroup(groups[1].name, groups[1].indexes)
	end
end

-- While the screen is open, notice when the player walks into or out of reach of a bench.
local function watch()
	watching += 1
	local token = watching
	benches = benchesNow()
	showTab(tab)
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

function CraftUI.init(hotbarUi)
	hotbar = hotbarUi
	local _, body = UIKit.window("craft", "조합", 860, 520, Enum.KeyCode.C, watch, function()
		watching += 1
	end)

	local x = 0
	for _, entry in { { "craft", "조합" }, { "hand", "손 작업" }, { "upgrade", "작업대 단계" } } do
		local item = UIKit.button(body, entry[2], 15)
		item.AutoButtonColor = false
		item.Size = UDim2.fromOffset(110, 30)
		item.Position = UDim2.fromOffset(x, 0)
		item.Activated:Connect(function()
			showTab(entry[1])
		end)
		tabButtons[entry[1]] = item
		x += 116
	end

	nearLabel = UIKit.label(body, "", 12)
	nearLabel.TextColor3 = UIKit.DIM
	nearLabel.TextXAlignment = Enum.TextXAlignment.Left
	nearLabel.TextWrapped = false
	nearLabel.TextTruncate = Enum.TextTruncate.AtEnd
	nearLabel.Position = UDim2.fromOffset(0, 38)
	nearLabel.Size = UDim2.new(1, 0, 0, 18)

	groupList = UIKit.scroller(body, nil, 5)
	groupList.ScrollBarThickness = 4
	groupList.Position = UDim2.fromOffset(0, 64)
	groupList.Size = UDim2.new(0, 190, 1, -64)

	rowList = UIKit.scroller(body, nil, 6)
	rowList.Position = UDim2.fromOffset(202, 64)
	rowList.Size = UDim2.new(1, -202, 1, -64)

	-- F on a workbench or a hand station opens this screen at what that one makes.
	Net.get("MachineInfo").OnClientEvent:Connect(function(message)
		if type(message) ~= "table" or message.kind ~= "bench" or type(message.info) ~= "table" then
			return
		end
		local kind = message.info.bench
		local onHand = kind == "hand_furnace" or kind == "campfire"
		Screens.open("craft")
		benches = benchesNow()
		showTab(if onHand then "hand" else "craft")
		local groups = if onHand
			then ScreenLogic.groups(Recipes.hand, "station")
			else ScreenLogic.groups(Recipes.craft, "bench")
		for _, entry in groups do
			if entry.name == kind then
				showGroup(entry.name, entry.indexes)
			end
		end
	end)

	-- The bag or the tiers changed: the same rows, with new numbers.
	hotbar.onChange(function()
		if Screens.isOpen("craft") then
			benches = benchesNow()
			refreshRows()
			refreshGroups()
		end
	end)
end

return CraftUI
