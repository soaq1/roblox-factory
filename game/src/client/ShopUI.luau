-- Two counters: a hub merchant's, and a vending machine's. Both only ask; the server decides.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local Prices = require(Shared:WaitForChild("Prices"))
local ShopLogic = require(Shared:WaitForChild("ShopLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local ShopUI = {}

local Stock = UIKit.Stock
local MERCHANT_NAMES = { farmer = "농부", miner = "광부", cook = "요리사", builder = "건축가" }
local ROW = 46

local hotbar

-- ------------------------------------------------------------------ merchants
local shopFrame: Frame
local sellList: ScrollingFrame
local buyList: ScrollingFrame
local shopCoins: TextLabel
local merchant: string? = nil

local function sortedKeys(list: { [string]: number }): { string }
	local keys = {}
	for key in list do
		table.insert(keys, key)
	end
	table.sort(keys, function(a, b)
		return Stock.name(a) < Stock.name(b)
	end)
	return keys
end

-- One line of a counter: picture, name, a line of detail, and buttons on the right.
local function row(
	parent: Instance,
	key: string,
	detail: string,
	actions: { { text: string, run: () -> () } }
): Frame
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(1, -8, 0, ROW)
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	frame.Parent = parent
	UIKit.round(frame, 6)

	local art = Instance.new("Frame")
	art.BackgroundTransparency = 1
	art.Position = UDim2.fromOffset(4, 4)
	art.Size = UDim2.fromOffset(ROW - 8, ROW - 8)
	art.Parent = frame
	UIKit.picture(art, key)

	local right = #actions * 50 + 6
	local name = UIKit.label(frame, Stock.name(key), 13)
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.TextTruncate = Enum.TextTruncate.AtEnd
	name.TextWrapped = false
	name.Position = UDim2.fromOffset(ROW, 4)
	name.Size = UDim2.new(1, -ROW - right, 0, 19)
	local sub = UIKit.label(frame, detail, 12)
	sub.TextColor3 = UIKit.DIM
	sub.TextXAlignment = Enum.TextXAlignment.Left
	sub.TextTruncate = Enum.TextTruncate.AtEnd
	sub.TextWrapped = false
	sub.Position = UDim2.fromOffset(ROW, 23)
	sub.Size = UDim2.new(1, -ROW - right, 0, 18)

	for i, action in actions do
		local press = UIKit.button(frame, action.text, 12)
		press.BackgroundColor3 = UIKit.LINE
		press.Size = UDim2.fromOffset(46, 28)
		press.Position = UDim2.new(1, -(#actions - i + 1) * 50, 0.5, -14)
		press.Activated:Connect(action.run)
	end
	return frame
end

local function note(parent: Instance, text: string)
	local label = UIKit.label(parent, text, 13)
	label.TextColor3 = UIKit.DIM
	label.Size = UDim2.new(1, -8, 0, 40)
end

local function drawShop()
	local id = merchant
	if not id then
		return
	end
	local bag, coins = hotbar.bag, hotbar.state.coins
	shopCoins.Text = "가진 코인 " .. UIKit.number(coins)

	UIKit.clear(sellList)
	local sells = Prices.sells[id]
	if sells then
		for order, key in sortedKeys(sells) do
			local function buy(n: number)
				return function()
					Net.get("ShopAct"):FireServer(id, "buy", key, n)
				end
			end
			local most = ShopLogic.affordable(coins, sells, key)
			local line = row(sellList, key, sells[key] .. "코인 · 가진 것 " .. (bag[key] or 0), {
				{ text = "1", run = buy(1) },
				{ text = "10", run = buy(10) },
				{ text = "최대", run = buy(math.max(most, 1)) },
			})
			line.LayoutOrder = order
		end
	else
		note(sellList, "이 상인은 파는 것이 없습니다")
	end

	UIKit.clear(buyList)
	local buys = Prices.buys[id]
	if buys then
		local shown = 0
		for order, key in sortedKeys(buys) do
			local have = bag[key] or 0
			if have > 0 then
				shown += 1
				local function sell(n: number)
					return function()
						Net.get("ShopAct"):FireServer(id, "sell", key, math.min(n, ShopLogic.MAX_AT_ONCE))
					end
				end
				local line = row(buyList, key, "개당 " .. buys[key] .. "코인 · 가진 것 " .. have, {
					{ text = "1", run = sell(1) },
					{ text = "10", run = sell(math.min(10, have)) },
					{ text = "전부", run = sell(have) },
				})
				line.LayoutOrder = order
			end
		end
		if shown == 0 then
			local names = {}
			for _, key in sortedKeys(buys) do
				table.insert(names, Stock.name(key))
			end
			note(buyList, "사 주는 것: " .. table.concat(names, ", "))
		end
	else
		note(buyList, "이 상인은 사 주는 것이 없습니다")
	end
end

local function openShop(payload: any)
	-- The hub sends the merchant's id, alone or inside a table.
	local id = if type(payload) == "table" then payload.merchant or payload.id else payload
	if type(id) ~= "string" or not (Prices.sells[id] or Prices.buys[id]) then
		return
	end
	merchant = id
	local title = shopFrame:FindFirstChild("Title")
	if title and title:IsA("TextLabel") then
		title.Text = (MERCHANT_NAMES[id] or id) .. "의 가게"
	end
	Screens.open("shop")
	drawShop()
end

local function column(body: Frame, heading: string, x: UDim): ScrollingFrame
	local title = UIKit.label(body, heading, 14)
	title.TextXAlignment = Enum.TextXAlignment.Left
	title.Position = UDim2.new(x, UDim.new(0, 0))
	title.Size = UDim2.new(0.5, -8, 0, 22)
	local list = UIKit.scroller(body, nil, 5)
	list.Position = UDim2.new(x, UDim.new(0, 26))
	list.Size = UDim2.new(0.5, -8, 1, -26)
	return list
end

local function buildShop()
	local frame, body = UIKit.window("shop", "가게", 760, 440)
	shopFrame = frame
	shopCoins = UIKit.label(frame, "", 14)
	shopCoins.TextXAlignment = Enum.TextXAlignment.Right
	shopCoins.TextColor3 = UIKit.PICK
	shopCoins.Position = UDim2.new(1, -270, 0, 10)
	shopCoins.Size = UDim2.fromOffset(200, 26)
	sellList = column(body, "파는 것", UDim.new(0, 0))
	buyList = column(body, "사 주는 것 (가방에 있는 것만 보임)", UDim.new(0.5, 8))
end

-- ------------------------------------------------------------------ vending machines
local vendBody: Frame
local current: any = nil -- the last MachineInfo for a vending machine
-- What the player has typed or picked but not yet sent.
local draft = { item = nil :: string?, price = "", limit = "", mode = "sell", amount = "1" }

local function act(action: string, arg: any)
	if current then
		Net.get("MachineAct"):FireServer(current.owner, current.x, current.y, current.z, action, arg)
	end
end

local function field(
	parent: Instance,
	caption: string,
	text: string,
	x: number,
	y: number,
	width: number,
	changed: (string) -> ()
): (TextBox, TextLabel)
	local label = UIKit.label(parent, caption, 12)
	label.TextColor3 = UIKit.DIM
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Position = UDim2.fromOffset(x, y)
	label.Size = UDim2.fromOffset(width, 16)
	local box = UIKit.input(parent, "0", 14, true)
	box.Position = UDim2.fromOffset(x, y + 18)
	box.Size = UDim2.fromOffset(width, 30)
	box.Text = text
	box:GetPropertyChangedSignal("Text"):Connect(function()
		changed(box.Text)
	end)
	return box, label
end

local function text(
	parent: Instance,
	value: string,
	size: number,
	x: number,
	y: number,
	width: number,
	height: number
): TextLabel
	local label = UIKit.label(parent, value, size)
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextYAlignment = Enum.TextYAlignment.Top
	label.Position = UDim2.fromOffset(x, y)
	label.Size = UDim2.fromOffset(width, height)
	return label
end

local function amount(): number
	return tonumber(draft.amount) or 0
end

-- The left half, the same for everyone: what the machine deals in and how much it holds.
local function drawStatus(info): number
	local art = Instance.new("Frame")
	art.BackgroundColor3 = UIKit.PANEL
	art.BorderSizePixel = 0
	art.Size = UDim2.fromOffset(96, 96)
	art.Parent = vendBody
	UIKit.round(art, 8)
	if info.item then
		UIKit.picture(art, info.item)
	end
	local y = 0
	if not info.item or info.price < 1 then
		text(vendBody, "아직 설정되지 않은 자판기입니다", 14, 108, y, 190, 40)
		return 104
	end
	text(vendBody, (if info.mode == "sell" then "팝니다" else "삽니다"), 13, 108, y, 190, 18).TextColor3 =
		UIKit.PICK
	text(vendBody, Stock.name(info.item), 16, 108, y + 20, 190, 22)
	text(vendBody, "개당 " .. UIKit.number(info.price) .. "코인", 14, 108, y + 44, 190, 20)
	local holding = if info.mode == "sell"
		then "재고 " .. info.stock
		else "모은 것 "
			.. info.stock
			.. " / "
			.. info.limit
			.. " · 지금 "
			.. info.wanted
			.. "개 더 삼"
	text(vendBody, holding, 13, 108, y + 66, 200, 34).TextColor3 = UIKit.DIM
	return 104
end

local function drawVisitor(info, y: number)
	if not info.item or info.price < 1 then
		return
	end
	field(vendBody, "개수", draft.amount, 0, y + 6, 96, function(value)
		draft.amount = value
	end)
	local have = hotbar.bag[info.item] or 0
	local selling = info.mode == "sell"
	local press = UIKit.button(vendBody, if selling then "사기" else "팔기", 15)
	press.BackgroundColor3 = UIKit.LINE
	press.Position = UDim2.fromOffset(108, y + 24)
	press.Size = UDim2.fromOffset(90, 30)
	press.Activated:Connect(function()
		act(if selling then "buy" else "sell", amount())
	end)
	text(
		vendBody,
		"가진 것 " .. have .. " · 코인 " .. UIKit.number(hotbar.state.coins),
		13,
		0,
		y + 64,
		300,
		20
	).TextColor3 =
		UIKit.DIM
	text(vendBody, info.ownerName .. "님의 자판기", 13, 0, y + 88, 300, 20).TextColor3 = UIKit.DIM
end

local function drawOwner(info, y: number)
	-- stock in and out
	field(vendBody, "개수", draft.amount, 0, y + 6, 96, function(value)
		draft.amount = value
	end)
	local put = UIKit.button(vendBody, "넣기", 14)
	put.BackgroundColor3 = UIKit.LINE
	put.Position = UDim2.fromOffset(108, y + 24)
	put.Size = UDim2.fromOffset(70, 30)
	put.Activated:Connect(function()
		act("deposit", amount())
	end)
	local out = UIKit.button(vendBody, "꺼내기", 14)
	out.BackgroundColor3 = UIKit.LINE
	out.Position = UDim2.fromOffset(184, y + 24)
	out.Size = UDim2.fromOffset(70, 30)
	out.Activated:Connect(function()
		act("withdraw", amount())
	end)
	if info.item then
		text(vendBody, "가방에 " .. (hotbar.bag[info.item] or 0) .. "개", 13, 0, y + 60, 280, 18).TextColor3 =
			UIKit.DIM
	end

	-- settings
	local top = y + 88
	field(vendBody, "개당 가격", draft.price, 0, top, 96, function(value)
		draft.price = value
	end)
	local limitBox, limitCaption = field(
		vendBody,
		"몇 개까지 살지",
		draft.limit,
		108,
		top,
		96,
		function(value)
			draft.limit = value
		end
	)
	limitBox.Visible = draft.mode == "buy"
	limitCaption.Visible = draft.mode == "buy"
	local mode =
		UIKit.button(vendBody, if draft.mode == "sell" then "방식: 팔기" else "방식: 사기", 13)
	mode.Position = UDim2.fromOffset(0, top + 56)
	mode.Size = UDim2.fromOffset(120, 30)
	local save = UIKit.button(vendBody, "설정 저장", 14)
	save.BackgroundColor3 = UIKit.LINE
	save.Position = UDim2.fromOffset(128, top + 56)
	save.Size = UDim2.fromOffset(110, 30)
	save.Activated:Connect(function()
		act("configure", {
			item = draft.item,
			price = tonumber(draft.price) or 0,
			mode = draft.mode,
			limit = tonumber(draft.limit) or 0,
		})
	end)
	local chosen = text(
		vendBody,
		"다룰 물건: " .. (if draft.item then Stock.name(draft.item) else "오른쪽에서 고르세요"),
		13,
		0,
		top + 92,
		300,
		36
	)
	chosen.TextColor3 = UIKit.DIM

	-- what to deal in: anything in the bag
	local heading = text(vendBody, "다룰 물건 고르기 (가방에 있는 것)", 13, 320, 0, 300, 18)
	heading.TextColor3 = UIKit.DIM
	local grid = UIKit.scroller(vendBody, Vector2.new(84, 90), 6)
	grid.Position = UDim2.fromOffset(320, 22)
	grid.Size = UDim2.new(1, -320, 1, -22)
	local keys = {}
	for key in hotbar.bag do
		table.insert(keys, key)
	end
	if draft.item and not hotbar.bag[draft.item] then
		table.insert(keys, draft.item)
	end
	table.sort(keys, function(a, b)
		return Stock.name(a) < Stock.name(b)
	end)
	local strokes: { [string]: UIStroke } = {}
	for order, key in keys do
		local tile = UIKit.tile(grid, key, 84, 90, Stock.name(key) .. " " .. (hotbar.bag[key] or 0))
		tile.LayoutOrder = order
		local stroke = tile:FindFirstChildOfClass("UIStroke")
		if stroke then
			strokes[key] = stroke
			stroke.Color = if key == draft.item then UIKit.PICK else UIKit.LINE
			stroke.Thickness = if key == draft.item then 3 else 1
		end
		UIKit.cover(tile, function()
			draft.item = key
			chosen.Text = "다룰 물건: " .. Stock.name(key)
			for other, mark in strokes do
				mark.Color = if other == key then UIKit.PICK else UIKit.LINE
				mark.Thickness = if other == key then 3 else 1
			end
		end)
	end

	mode.Activated:Connect(function()
		draft.mode = if draft.mode == "sell" then "buy" else "sell"
		mode.Text = if draft.mode == "sell" then "방식: 팔기" else "방식: 사기"
		limitBox.Visible = draft.mode == "buy"
		limitCaption.Visible = draft.mode == "buy"
	end)
end

local function drawVending()
	local info = current and current.info
	if not info then
		return
	end
	UIKit.clear(vendBody)
	local y = drawStatus(info)
	if info.isOwner then
		drawOwner(info, y)
	else
		drawVisitor(info, y)
	end
end

local function sameMachine(a: any, b: any): boolean
	return a ~= nil and b ~= nil and a.owner == b.owner and a.x == b.x and a.y == b.y and a.z == b.z
end

local function onMachineInfo(payload: any)
	if type(payload) ~= "table" or payload.kind ~= "vending" or type(payload.info) ~= "table" then
		return
	end
	local info = payload.info
	-- A different machine, or one whose settings changed: start the form from what the machine has.
	if not sameMachine(current, payload) or not Screens.isOpen("vending") then
		draft.amount = "1"
		draft.item = info.item
		draft.price = if info.price >= 1 then tostring(info.price) else ""
		draft.limit = tostring(info.limit)
		draft.mode = info.mode
	end
	current = payload
	Screens.open("vending")
	drawVending()
end

local function buildVending()
	local _, body = UIKit.window("vending", "자판기", 700, 400)
	vendBody = body
end

function ShopUI.init(hotbarUi)
	hotbar = hotbarUi
	buildShop()
	buildVending()
	Net.get("Shop").OnClientEvent:Connect(openShop)
	Net.get("MachineInfo").OnClientEvent:Connect(onMachineInfo)
	-- Counts and coins on an open counter follow the bag.
	hotbar.onChange(function()
		if Screens.isOpen("shop") then
			drawShop()
		elseif Screens.isOpen("vending") and not UserInputService:GetFocusedTextBox() then
			-- not while a number is being typed: redrawing would take the box away
			drawVending()
		end
	end)
end

return ShopUI
