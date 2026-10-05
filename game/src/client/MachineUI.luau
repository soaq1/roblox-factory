-- The inside of a machine.
--
-- Every processing machine has slots: ingredients (and fuel, if it burns any) and finished
-- products. Belts fill and empty them; this window lets the player do the same by hand, the way a
-- furnace is used in Minecraft. The machine's slots are on the left with what it can make, the
-- player's bag on the right. Pressing something in the bag puts it into the machine; pressing a
-- slot brings its contents back. An assembler's window also has the list of things it can be told
-- to make.
--
-- The server opens the window (through "MachineInfo") when the owner presses F on the machine and
-- keeps sending what is inside while it stays open. Everything the player does goes back through
-- "MachineAct"; the server decides what actually moves.
--
-- The sorter's "which item to pick out" list lives here too.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local AssemblyLogic = require(Shared:WaitForChild("AssemblyLogic"))
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local ProcessLogic = require(Shared:WaitForChild("ProcessLogic"))
local Recipes = require(Shared:WaitForChild("Recipes"))
local StatusText = require(Shared:WaitForChild("StatusText"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local MachineUI = {}

local WINDOW = "machine"
local SORTER = "sorter"
local TILE_W, TILE_H = 78, 88
local ROW = 52
local LEFT = 430 -- width of the machine's side of the window

type Target = { owner: number, x: number, y: number, z: number, id: string }

local hotbar
local target: Target? = nil
local info: { [string]: any } = {}

-- the machine window
local title: TextLabel
local statusLabel: TextLabel
local lamp: Frame
local fuelLabel: TextLabel
local inSlots: ScrollingFrame
local outSlots: ScrollingFrame
local recipesTitle: TextLabel
local recipeList: ScrollingFrame
local bagTitle: TextLabel
local bagGrid: ScrollingFrame
local bagEmpty: TextLabel
-- What each part last drew, so a part is rebuilt only when what it shows has changed.
local drawn: { [string]: string } = {}

-- the sorter's window
local sorterTarget: Target? = nil
local sorterGrid: ScrollingFrame

local function act(at: Target?, action: string, arg: any)
	if at then
		Net.get("MachineAct"):FireServer(at.owner, at.x, at.y, at.z, action, arg)
	end
end

local function amounts(bag: { [string]: number }): string
	local parts = {}
	for key, n in bag do
		table.insert(parts, Defs.name(key) .. " " .. n)
	end
	table.sort(parts)
	return table.concat(parts, " · ")
end

-- A bag of counts as a stable string, for noticing change.
local function signature(bag: { [string]: number }): string
	local parts = {}
	for key, n in bag do
		table.insert(parts, key .. "=" .. n)
	end
	table.sort(parts)
	return table.concat(parts, ",")
end

local function sortedKeys(bag: { [string]: number }): { string }
	local keys = {}
	for key in bag do
		table.insert(keys, key)
	end
	table.sort(keys, function(a, b)
		local na, nb = Defs.name(a), Defs.name(b)
		if na ~= nb then
			return na < nb
		end
		return a < b
	end)
	return keys
end

-- The recipes the machine is working from right now.
local function currentRecipes(): { any }
	local at = target
	if not at then
		return {}
	end
	if type(info.choices) == "table" then
		-- an assembler: the one recipe it has been set to, if any
		local recipe = Recipes.craft[info.current]
		return if recipe then { AssemblyLogic.toProcess(recipe) } else {}
	end
	return Recipes.byMachine[at.id] or {}
end

-- Fills a row of slots with one tile for each kind of item in it.
local function drawSlots(name: string, frame: ScrollingFrame, contents: { [string]: number }, slot: string)
	local sig = signature(contents)
	if drawn[name] == sig then
		return
	end
	drawn[name] = sig
	UIKit.clear(frame)
	for order, id in sortedKeys(contents) do
		local tile = UIKit.tile(frame, "item:" .. id, TILE_W, TILE_H, Defs.name(id) .. " " .. contents[id])
		tile.LayoutOrder = order
		UIKit.cover(tile, function()
			act(target, "take", { slot = slot, id = id })
		end)
	end
end

-- One line of the "what it makes" list for an ordinary machine.
local function plainRecipe(order: number, recipe)
	local row = UIKit.label(
		recipeList,
		amounts(recipe.ins) .. "  →  " .. amounts(recipe.outs) .. "  ·  " .. recipe.secs .. "초",
		13
	)
	row.LayoutOrder = order
	row.TextXAlignment = Enum.TextXAlignment.Left
	row.TextWrapped = false
	row.TextTruncate = Enum.TextTruncate.AtEnd
	row.Size = UDim2.new(1, -10, 0, 22)
end

-- One line of an assembler's "what to make" list: pressing it sets the machine to that recipe.
local function choiceRow(order: number, index: number, chosen: boolean)
	local recipe = Recipes.craft[index]
	if not recipe then
		return
	end
	local row = Instance.new("Frame")
	row.Size = UDim2.new(1, -10, 0, ROW)
	row.BackgroundColor3 = UIKit.PANEL
	row.BorderSizePixel = 0
	row.LayoutOrder = order
	UIKit.round(row, 8)
	UIKit.stroke(row, if chosen then UIKit.PICK else UIKit.LINE, if chosen then 2 else 1)

	local art = Instance.new("Frame")
	art.BackgroundTransparency = 1
	art.Position = UDim2.fromOffset(6, 4)
	art.Size = UDim2.fromOffset(ROW - 8, ROW - 8)
	art.Parent = row
	UIKit.picture(art, "item:" .. recipe.out)

	local name =
		UIKit.label(row, Defs.name(recipe.out) .. (if recipe.n > 1 then " ×" .. recipe.n else ""), 14)
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.Position = UDim2.fromOffset(ROW + 6, 5)
	name.Size = UDim2.new(1, -ROW - 16, 0, 20)

	local needs = UIKit.label(row, amounts(recipe.ins), 12)
	needs.TextColor3 = UIKit.DIM
	needs.TextXAlignment = Enum.TextXAlignment.Left
	needs.TextTruncate = Enum.TextTruncate.AtEnd
	needs.TextWrapped = false
	needs.Position = UDim2.fromOffset(ROW + 6, 26)
	needs.Size = UDim2.new(1, -ROW - 16, 0, 20)

	UIKit.cover(row, function()
		act(target, "recipe", if chosen then 0 else index)
	end)
	row.Parent = recipeList
end

local function drawRecipes()
	local at = target
	if not at then
		return
	end
	local picker = type(info.choices) == "table"
	local sig = at.id .. "|" .. (if picker then #info.choices .. ":" .. tostring(info.current) else "fixed")
	if drawn.recipes == sig then
		return
	end
	drawn.recipes = sig
	UIKit.clear(recipeList)
	recipeList.CanvasPosition = Vector2.zero
	if picker then
		recipesTitle.Text = "만들 것 고르기 · 고른 것을 다시 누르면 만들지 않음"
		for order, index in info.choices do
			if type(index) == "number" then
				choiceRow(order, index, index == info.current)
			end
		end
	else
		recipesTitle.Text = "이 기계가 만드는 것"
		for order, recipe in Recipes.byMachine[at.id] or {} do
			plainRecipe(order, recipe)
		end
	end
end

-- The player's side: the things in the bag that this machine takes.
local function drawBag()
	if not target then
		return
	end
	local wanted = ProcessLogic.wanted(currentRecipes(), info.usesFuel == true, Recipes.fuel)
	local offered: { [string]: number } = {}
	for key, n in hotbar.bag do
		if wanted[key] and Defs.Items[key] then
			offered[key] = n
		end
	end
	local sig = signature(offered)
	if drawn.bag == sig then
		return
	end
	drawn.bag = sig
	UIKit.clear(bagGrid)
	local keys = sortedKeys(offered)
	bagEmpty.Visible = #keys == 0
	bagEmpty.Text = if next(wanted) == nil
		then "먼저 이 기계가 만들 것을 골라 주세요."
		else "가방에 이 기계가 받는 것이 없습니다."
	for order, id in keys do
		local tile = UIKit.tile(bagGrid, "item:" .. id, TILE_W, TILE_H, Defs.name(id) .. " " .. offered[id])
		tile.LayoutOrder = order
		UIKit.cover(tile, function()
			-- as many as fit: the server works out how many that is
			act(target, "put", { id = id, n = hotbar.bag[id] or 0 })
		end)
	end
end

local function drawStatus()
	local code = if type(info.status) == "string" then info.status else ""
	local colour = StatusText.COLOR[code] or StatusText.COLOR.unset
	lamp.BackgroundColor3 = Color3.fromRGB(colour[1], colour[2], colour[3])
	local parts = { StatusText.of(code) }
	if info.boosted then
		table.insert(parts, "전기로 가속")
	end
	if type(info.rate) == "number" and info.rate > 0 then
		table.insert(parts, StatusText.rate(info.rate))
	end
	statusLabel.Text = table.concat(parts, "  ·  ")
	fuelLabel.Visible = info.usesFuel == true
	if info.usesFuel then
		local heat = if type(info.fuel) == "number" then info.fuel else 0
		fuelLabel.Text = if heat > 0
			then "불: 앞으로 " .. heat .. "번 더 일할 수 있음 · 땔감은 재료 칸에 넣습니다"
			else "불이 꺼져 있음 · 통나무, 숯, 석탄 같은 땔감을 재료 칸에 넣으세요"
	end
end

local function draw()
	local at = target
	if not at then
		return
	end
	title.Text = Defs.name(at.id)
	drawStatus()
	drawSlots("in", inSlots, if type(info.buf) == "table" then info.buf else {}, "buf")
	drawSlots("out", outSlots, if type(info.out) == "table" then info.out else {}, "out")
	drawRecipes()
	drawBag()
end

local function sameTarget(payload): boolean
	local at = target
	return at ~= nil
		and at.owner == payload.owner
		and at.x == payload.x
		and at.y == payload.y
		and at.z == payload.z
end

local function onMachine(payload)
	local update = payload.info.update == true
	-- A stale update for a window the player has already closed must not open it again.
	if update and not (Screens.isOpen(WINDOW) and sameTarget(payload)) then
		return
	end
	if not sameTarget(payload) then
		-- Leaving one machine's window for another's: tell the first it is no longer watched.
		act(target, "close", nil)
		drawn = {}
	end
	target = { owner = payload.owner, x = payload.x, y = payload.y, z = payload.z, id = payload.id }
	info = payload.info
	draw()
	Screens.open(WINDOW)
end

-- ------------------------------------------------------------------ the sorter

local function showSorter(payload)
	sorterTarget = { owner = payload.owner, x = payload.x, y = payload.y, z = payload.z, id = payload.id }
	UIKit.clear(sorterGrid)
	sorterGrid.CanvasPosition = Vector2.zero
	local order = 0
	for _, group in Defs.Palette do
		if group.tab == "아이템" then
			for _, entry in group.ids do
				local item = Defs.itemOf(entry)
				if item then
					order += 1
					local tile = UIKit.tile(sorterGrid, entry, 84, 84)
					tile.LayoutOrder = order
					if item == payload.info.current then
						local stroke = tile:FindFirstChildOfClass("UIStroke")
						if stroke then
							stroke.Color = UIKit.PICK
							stroke.Thickness = 3
						end
					end
					UIKit.cover(tile, function()
						act(sorterTarget, "filter", item)
						Screens.close(SORTER)
					end)
				end
			end
		end
	end
	Screens.open(SORTER)
end

local function onInfo(payload: any)
	if type(payload) ~= "table" or type(payload.info) ~= "table" then
		return
	end
	if payload.kind == "machine" then
		onMachine(payload)
	elseif payload.kind == "sorter" then
		showSorter(payload)
	end
	-- anything else is some other machine's screen
end

local function heading(parent: Instance, text: string, y: number, width: UDim): TextLabel
	local label = UIKit.label(parent, text, 12)
	label.TextColor3 = UIKit.DIM
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextWrapped = false
	label.TextTruncate = Enum.TextTruncate.AtEnd
	label.Position = UDim2.fromOffset(0, y)
	label.Size = UDim2.new(width.Scale, width.Offset, 0, 18)
	return label
end

-- A row of slots: tiles side by side, scrolling sideways if there are many.
local function slotRow(parent: Instance, y: number): ScrollingFrame
	local frame = Instance.new("ScrollingFrame")
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BackgroundTransparency = 0.5
	frame.BorderSizePixel = 0
	frame.ScrollBarThickness = 4
	frame.ScrollingDirection = Enum.ScrollingDirection.X
	frame.CanvasSize = UDim2.new()
	frame.AutomaticCanvasSize = Enum.AutomaticSize.X
	frame.Position = UDim2.fromOffset(0, y)
	frame.Size = UDim2.fromOffset(LEFT, TILE_H + 12)
	frame.Parent = parent
	UIKit.round(frame, 8)
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Parent = frame
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 6)
	pad.Parent = frame
	return frame
end

local function buildMachineWindow()
	local frame, body = UIKit.window(WINDOW, "", 900, 560, nil, nil, function()
		-- Closing the window tells the machine to stop sending what is inside it.
		act(target, "close", nil)
		target = nil
		drawn = {}
	end)
	title = frame:FindFirstChild("Title") :: TextLabel

	lamp = Instance.new("Frame")
	lamp.Size = UDim2.fromOffset(14, 14)
	lamp.Position = UDim2.fromOffset(0, 4)
	lamp.BorderSizePixel = 0
	lamp.Parent = body
	UIKit.round(lamp, 7)

	statusLabel = UIKit.label(body, "", 14)
	statusLabel.TextXAlignment = Enum.TextXAlignment.Left
	statusLabel.TextWrapped = false
	statusLabel.Position = UDim2.fromOffset(22, 0)
	statusLabel.Size = UDim2.fromOffset(LEFT - 22, 22)

	heading(body, "재료 칸 · 누르면 가방으로 돌아옴", 30, UDim.new(0, LEFT))
	inSlots = slotRow(body, 50)

	fuelLabel = UIKit.label(body, "", 12)
	fuelLabel.TextColor3 = UIKit.DIM
	fuelLabel.TextXAlignment = Enum.TextXAlignment.Left
	fuelLabel.TextWrapped = false
	fuelLabel.TextTruncate = Enum.TextTruncate.AtEnd
	fuelLabel.Position = UDim2.fromOffset(0, 50 + TILE_H + 16)
	fuelLabel.Size = UDim2.fromOffset(LEFT, 18)

	local outY = 50 + TILE_H + 40
	heading(body, "만든 것 · 누르면 가방으로", outY, UDim.new(0, LEFT))
	outSlots = slotRow(body, outY + 20)

	local recipesY = outY + 20 + TILE_H + 22
	recipesTitle = heading(body, "", recipesY, UDim.new(0, LEFT))
	recipeList = UIKit.scroller(body, nil, 5)
	recipeList.Position = UDim2.fromOffset(0, recipesY + 22)
	recipeList.Size = UDim2.new(0, LEFT, 1, -(recipesY + 22))

	bagTitle = heading(
		body,
		"내 가방 · 이 기계가 받는 것 · 누르면 들어갈 만큼 넣음",
		0,
		UDim.new(1, -(LEFT + 20))
	)
	bagTitle.Position = UDim2.fromOffset(LEFT + 20, 2)
	bagGrid = UIKit.scroller(body, Vector2.new(TILE_W, TILE_H), 8)
	bagGrid.Position = UDim2.fromOffset(LEFT + 20, 26)
	bagGrid.Size = UDim2.new(1, -(LEFT + 20), 1, -26)

	bagEmpty = UIKit.label(body, "", 13)
	bagEmpty.TextColor3 = UIKit.DIM
	bagEmpty.Position = UDim2.fromOffset(LEFT + 20, 70)
	bagEmpty.Size = UDim2.new(1, -(LEFT + 20), 0, 40)
	bagEmpty.Visible = false
end

local function buildSorterWindow()
	local _, body = UIKit.window(SORTER, "골라낼 것 정하기", 640, 470, nil, nil, function()
		sorterTarget = nil
	end)

	local clear = UIKit.button(body, "정하지 않음", 13)
	clear.Size = UDim2.fromOffset(110, 28)
	clear.Activated:Connect(function()
		act(sorterTarget, "filter", "")
		Screens.close(SORTER)
	end)

	local hint =
		UIKit.label(body, "고른 것만 옆 출구로 나가고 나머지는 그대로 지나갑니다.", 12)
	hint.TextColor3 = UIKit.DIM
	hint.TextXAlignment = Enum.TextXAlignment.Left
	hint.Position = UDim2.fromOffset(120, 0)
	hint.Size = UDim2.new(1, -120, 0, 28)

	sorterGrid = UIKit.scroller(body, Vector2.new(84, 84), 8)
	sorterGrid.Position = UDim2.fromOffset(0, 36)
	sorterGrid.Size = UDim2.new(1, 0, 1, -36)
end

function MachineUI.init(hotbarUi)
	hotbar = hotbarUi
	buildMachineWindow()
	buildSorterWindow()
	Net.get("MachineInfo").OnClientEvent:Connect(onInfo)
	-- The bag changed (something went in or came out): the player's side is drawn again.
	hotbar.onChange(function()
		if Screens.isOpen(WINDOW) then
			drawBag()
		end
	end)
end

return MachineUI
