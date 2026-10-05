-- The trade screen (T). With no trade open it lists who can be asked and who has asked; with one
-- open it shows both sides' offers and lets the player change their own.
-- Every change is a request to the server, which sends back the trade as it then stands.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local Screens = require(script.Parent.Screens)
local TileGrid = require(script.Parent.TileGrid)
local UIKit = require(script.Parent.UIKit)

local TradeUI = {}

local player = Players.LocalPlayer
local Stock = UIKit.Stock
local TILE_W, TILE_H = 78, 94

type SideView = { name: string, offer: { [string]: number }, coins: number, ready: boolean }
type Snapshot = { you: string, a: SideView, b: SideView }

local hotbar
local lobby: Frame
local tableFrame: Frame
local playerList: ScrollingFrame
local requestList: Frame
local lobbyNote: TextLabel
local notice: TextLabel
local mineTitle: TextLabel
local theirsTitle: TextLabel
local mineCoins: TextLabel
local theirsCoins: TextLabel
local theirsStroke: UIStroke
local mineTiles
local theirsTiles
local bagTiles
local amountBox: TextBox
local coinsBox: TextBox
local readyButton: TextButton

local current: Snapshot? = nil
local requests: { [number]: string } = {} -- who has asked me: user id -> name
local warned = false -- the other side changed their offer after I was ready

local function act(...: any)
	Net.get("TradeAct"):FireServer(...)
end

local function sides(snapshot: Snapshot): (SideView, SideView)
	if snapshot.you == "a" then
		return snapshot.a, snapshot.b
	end
	return snapshot.b, snapshot.a
end

local function listOf(offer: { [string]: number }): { any }
	return ScreenLogic.sorted(Defs, Stock, offer)
end

-- ---------------------------------------------------------------- nobody to trade with yet

local function drawRequests()
	UIKit.clear(requestList)
	local order = 0
	for id, name in requests do
		order += 1
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, 0, 0, 36)
		row.BackgroundColor3 = UIKit.PANEL
		row.BorderSizePixel = 0
		row.LayoutOrder = order
		row.Parent = requestList
		UIKit.round(row, 8)
		UIKit.stroke(row, UIKit.PICK, 2)
		local text = UIKit.label(row, name .. "님이 거래를 청했습니다", 14)
		text.TextXAlignment = Enum.TextXAlignment.Left
		text.Position = UDim2.fromOffset(12, 0)
		text.Size = UDim2.new(1, -120, 1, 0)
		local accept = UIKit.button(row, "받기", 14)
		accept.BackgroundColor3 = UIKit.BACK
		accept.Size = UDim2.fromOffset(90, 26)
		accept.Position = UDim2.new(1, -98, 0, 5)
		accept.Activated:Connect(function()
			-- Asking back is how a request is accepted.
			local other = Players:GetPlayerByUserId(id)
			if other then
				act("ask", other)
			else
				requests[id] = nil
				drawRequests()
			end
		end)
	end
	requestList.Size = UDim2.new(1, 0, 0, order * 42)
	playerList.Position = UDim2.fromOffset(0, order * 42 + 30)
	playerList.Size = UDim2.new(1, 0, 1, -(order * 42 + 30))
	lobbyNote.Position = UDim2.fromOffset(0, order * 42)
end

local function drawPlayers()
	UIKit.clear(playerList)
	local others = {}
	for _, other in Players:GetPlayers() do
		if other ~= player then
			table.insert(others, other)
		end
	end
	table.sort(others, function(a, b)
		return a.Name < b.Name
	end)
	lobbyNote.Text = if #others > 0
		then "거래할 사람을 고르세요. 상대가 받으면 거래가 열립니다."
		else "같은 서버에 다른 플레이어가 없습니다."
	for order, other in others do
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, -10, 0, 36)
		row.BackgroundColor3 = UIKit.PANEL
		row.BorderSizePixel = 0
		row.LayoutOrder = order
		row.Parent = playerList
		UIKit.round(row, 8)
		local shown = if other.DisplayName ~= other.Name
			then other.DisplayName .. " (" .. other.Name .. ")"
			else other.Name
		local text = UIKit.label(row, shown, 14)
		text.TextXAlignment = Enum.TextXAlignment.Left
		text.Position = UDim2.fromOffset(12, 0)
		text.Size = UDim2.new(1, -140, 1, 0)
		local ask = UIKit.button(row, "거래 청하기", 13)
		ask.BackgroundColor3 = UIKit.BACK
		ask.Size = UDim2.fromOffset(110, 26)
		ask.Position = UDim2.new(1, -118, 0, 5)
		ask.Activated:Connect(function()
			act("ask", other)
		end)
	end
end

-- ---------------------------------------------------------------- a trade is open

local function drawBag()
	-- Only what is not already all on the table is worth showing as "can add".
	bagTiles:set(ScreenLogic.sorted(Defs, Stock, hotbar.bag))
end

local function drawTable()
	local snapshot = current
	if not snapshot then
		return
	end
	local mine, theirs = sides(snapshot)
	mineTitle.Text = "나" .. (if mine.ready then " · 준비됨" else " · 준비 안 됨")
	mineTitle.TextColor3 = if mine.ready then UIKit.GOOD else UIKit.TEXT
	theirsTitle.Text = theirs.name .. (if theirs.ready then " · 준비됨" else " · 준비 안 됨")
	theirsTitle.TextColor3 = if theirs.ready then UIKit.GOOD else UIKit.TEXT
	mineCoins.Text = UIKit.number(mine.coins) .. "코인"
	theirsCoins.Text = UIKit.number(theirs.coins) .. "코인"
	mineTiles:set(listOf(mine.offer))
	theirsTiles:set(listOf(theirs.offer))
	readyButton.Text = if mine.ready then "준비 취소" else "준비"
	readyButton.BackgroundColor3 = if mine.ready then UIKit.LINE else UIKit.BACK
	notice.Text = if warned
		then "상대가 올린 것을 바꿨습니다. 준비가 풀렸으니 다시 확인하세요."
		else "둘 다 준비하면 한꺼번에 교환됩니다. 누가 올린 것을 바꾸면 양쪽 준비가 풀립니다."
	notice.TextColor3 = if warned then UIKit.PICK else UIKit.DIM
	theirsStroke.Color = if warned then UIKit.PICK else UIKit.LINE
	theirsStroke.Thickness = if warned then 3 else 1
	drawBag()
end

local function showPage()
	local trading = current ~= nil
	lobby.Visible = not trading
	tableFrame.Visible = trading
	if trading then
		drawTable()
	else
		drawRequests()
		drawPlayers()
	end
end

-- Pressing something in my bag puts that many more of it on the table.
local function addFromBag(key: string)
	local snapshot = current
	if not snapshot then
		return
	end
	local mine = sides(snapshot)
	local held = hotbar.bag[key] or 0
	local already = mine.offer[key] or 0
	local more = math.max(1, ScreenLogic.amount(amountBox.Text, held))
	local total = math.min(held, already + more)
	if total > already then
		act("offer", key, total)
	else
		UIKit.toast("가진 것을 이미 모두 올렸습니다")
	end
end

local function onTrade(payload: any)
	if payload == nil then
		current = nil
		warned = false
		if Screens.isOpen("trade") then
			showPage()
		end
		return
	end
	if type(payload) ~= "table" then
		return
	end
	if type(payload.request) == "table" then
		requests[payload.request.id] = tostring(payload.request.name)
		if Screens.isOpen("trade") and not current then
			showPage()
		end
		return
	end
	if payload.withdrawn then
		requests[payload.withdrawn] = nil
		if Screens.isOpen("trade") and not current then
			showPage()
		end
		return
	end
	if payload.you ~= "a" and payload.you ~= "b" then
		return
	end
	local snapshot = payload :: Snapshot
	if ScreenLogic.wasUnreadied(current, snapshot, snapshot.you) then
		warned = true
	elseif sides(snapshot).ready then
		-- I have looked again and agreed.
		warned = false
	end
	if not current then
		-- A trade has just opened: whoever asked is no longer waiting.
		requests = {}
	end
	current = snapshot
	if Screens.isOpen("trade") then
		showPage()
	else
		Screens.open("trade")
	end
end

local function column(parent: Frame, x: UDim, title: string): (TextLabel, TextLabel, ScrollingFrame, UIStroke)
	local frame = Instance.new("Frame")
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	frame.Position = UDim2.new(x.Scale, x.Offset, 0, 26)
	frame.Size = UDim2.new(0.5, -4, 0, 158)
	frame.Parent = parent
	UIKit.round(frame, 8)
	local stroke = UIKit.stroke(frame)
	local heading = UIKit.label(frame, title, 14)
	heading.TextXAlignment = Enum.TextXAlignment.Left
	heading.TextWrapped = false
	heading.Position = UDim2.fromOffset(10, 4)
	heading.Size = UDim2.new(1, -130, 0, 20)
	local coins = UIKit.label(frame, "0코인", 14)
	coins.TextXAlignment = Enum.TextXAlignment.Right
	coins.TextWrapped = false
	coins.TextColor3 = UIKit.PICK
	coins.Position = UDim2.new(1, -124, 0, 4)
	coins.Size = UDim2.fromOffset(114, 20)
	local grid = UIKit.scroller(frame, Vector2.new(TILE_W, TILE_H), 6)
	grid.Position = UDim2.fromOffset(8, 28)
	grid.Size = UDim2.new(1, -16, 1, -34)
	return heading, coins, grid, stroke
end

local function buildLobby(body: Frame)
	lobby = Instance.new("Frame")
	lobby.BackgroundTransparency = 1
	lobby.Size = UDim2.fromScale(1, 1)
	lobby.Parent = body

	requestList = Instance.new("Frame")
	requestList.BackgroundTransparency = 1
	requestList.Size = UDim2.fromScale(1, 0)
	requestList.Parent = lobby
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = requestList

	lobbyNote = UIKit.label(lobby, "", 13)
	lobbyNote.TextColor3 = UIKit.DIM
	lobbyNote.TextXAlignment = Enum.TextXAlignment.Left
	lobbyNote.Size = UDim2.new(1, 0, 0, 24)

	playerList = UIKit.scroller(lobby, nil, 6)
	playerList.Position = UDim2.fromOffset(0, 30)
	playerList.Size = UDim2.new(1, 0, 1, -30)
end

local function buildTable(body: Frame)
	tableFrame = Instance.new("Frame")
	tableFrame.BackgroundTransparency = 1
	tableFrame.Size = UDim2.fromScale(1, 1)
	tableFrame.Visible = false
	tableFrame.Parent = body

	notice = UIKit.label(tableFrame, "", 13)
	notice.TextXAlignment = Enum.TextXAlignment.Left
	notice.TextWrapped = false
	notice.TextTruncate = Enum.TextTruncate.AtEnd
	notice.Size = UDim2.new(1, 0, 0, 20)

	local mineGrid, theirsGrid
	mineTitle, mineCoins, mineGrid = column(tableFrame, UDim.new(0, 0), "나")
	theirsTitle, theirsCoins, theirsGrid, theirsStroke = column(tableFrame, UDim.new(0.5, 4), "상대")
	-- Pressing something I put up takes it back off the table.
	mineTiles = TileGrid.new(mineGrid, TILE_W, TILE_H, function(key)
		act("offer", key, 0)
	end)
	theirsTiles = TileGrid.new(theirsGrid, TILE_W, TILE_H, function() end)

	local bagTitle = UIKit.label(tableFrame, "내 가방 · 누르면 올립니다 · 한 번에", 13)
	bagTitle.TextColor3 = UIKit.DIM
	bagTitle.TextXAlignment = Enum.TextXAlignment.Left
	bagTitle.TextWrapped = false
	bagTitle.Position = UDim2.fromOffset(0, 194)
	bagTitle.Size = UDim2.fromOffset(240, 26)
	amountBox = UIKit.input(tableFrame, "개수", 13, true)
	amountBox.Text = "1"
	amountBox.Position = UDim2.fromOffset(244, 194)
	amountBox.Size = UDim2.fromOffset(70, 26)
	local each = UIKit.label(tableFrame, "개씩 · 올린 것을 누르면 내립니다", 13)
	each.TextColor3 = UIKit.DIM
	each.TextXAlignment = Enum.TextXAlignment.Left
	each.TextWrapped = false
	each.Position = UDim2.fromOffset(322, 194)
	each.Size = UDim2.fromOffset(300, 26)

	local bagGrid = UIKit.scroller(tableFrame, Vector2.new(TILE_W, TILE_H), 6)
	bagGrid.Position = UDim2.fromOffset(0, 226)
	bagGrid.Size = UDim2.new(1, 0, 1, -(226 + 44))
	bagTiles = TileGrid.new(bagGrid, TILE_W, TILE_H, addFromBag)

	-- The bottom line: coins on the left, ready and cancel on the right.
	coinsBox = UIKit.input(tableFrame, "코인", 14, true)
	coinsBox.AnchorPoint = Vector2.new(0, 1)
	coinsBox.Position = UDim2.fromScale(0, 1)
	coinsBox.Size = UDim2.fromOffset(130, 32)
	local setCoins = UIKit.button(tableFrame, "코인 올리기", 13)
	setCoins.AnchorPoint = Vector2.new(0, 1)
	setCoins.Position = UDim2.new(0, 138, 1, 0)
	setCoins.Size = UDim2.fromOffset(110, 32)
	setCoins.Activated:Connect(function()
		act("coins", ScreenLogic.amount(coinsBox.Text, hotbar.state.coins))
	end)

	local cancel = UIKit.button(tableFrame, "거래 취소", 13)
	cancel.AnchorPoint = Vector2.new(1, 1)
	cancel.Position = UDim2.fromScale(1, 1)
	cancel.Size = UDim2.fromOffset(100, 32)
	cancel.TextColor3 = UIKit.BAD
	cancel.Activated:Connect(function()
		act("cancel")
	end)
	readyButton = UIKit.button(tableFrame, "준비", 14)
	readyButton.AutoButtonColor = false
	readyButton.AnchorPoint = Vector2.new(1, 1)
	readyButton.Position = UDim2.new(1, -108, 1, 0)
	readyButton.Size = UDim2.fromOffset(130, 32)
	readyButton.Activated:Connect(function()
		local snapshot = current
		if snapshot then
			act("ready", not sides(snapshot).ready)
		end
	end)
end

function TradeUI.init(hotbarUi)
	hotbar = hotbarUi
	local _, body = UIKit.window("trade", "거래", 780, 520, Enum.KeyCode.T, showPage)
	buildLobby(body)
	buildTable(body)

	Net.get("Trade").OnClientEvent:Connect(onTrade)
	hotbar.onChange(function()
		if Screens.isOpen("trade") and current then
			drawBag()
		end
	end)
	local function playersChanged(gone: Player?)
		if gone then
			requests[gone.UserId] = nil
		end
		if Screens.isOpen("trade") and not current then
			showPage()
		end
	end
	Players.PlayerAdded:Connect(function()
		playersChanged(nil)
	end)
	Players.PlayerRemoving:Connect(playersChanged)
end

return TradeUI
