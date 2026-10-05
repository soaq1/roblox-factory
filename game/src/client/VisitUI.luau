-- The list of islands on this server, to go and look at, and the way home. Opens with V.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local UIKit = require(script.Parent.UIKit)

local VisitUI = {}

local list: ScrollingFrame
local whereLabel: TextLabel

local function draw(payload: any)
	if type(payload) ~= "table" or type(payload.islands) ~= "table" then
		return
	end
	local me = Players.LocalPlayer.UserId
	local hostName = "내 섬"
	UIKit.clear(list)
	local others = 0
	for order, entry in payload.islands do
		if type(entry) == "table" and type(entry.userId) == "number" then
			local name = tostring(entry.name or entry.user or entry.userId)
			if entry.userId == payload.at and entry.userId ~= me then
				hostName = name .. "님의 섬"
			end
			if entry.userId ~= me then
				others += 1
				local row = Instance.new("Frame")
				row.Size = UDim2.new(1, -8, 0, 40)
				row.BackgroundColor3 = UIKit.PANEL
				row.BorderSizePixel = 0
				row.LayoutOrder = order
				row.Parent = list
				UIKit.round(row, 6)
				local label = UIKit.label(row, name .. "님의 섬", 14)
				label.TextXAlignment = Enum.TextXAlignment.Left
				label.TextTruncate = Enum.TextTruncate.AtEnd
				label.TextWrapped = false
				label.Position = UDim2.fromOffset(12, 0)
				label.Size = UDim2.new(1, -90, 1, 0)
				local go = UIKit.button(row, if entry.userId == payload.at then "여기" else "가기", 13)
				go.BackgroundColor3 = UIKit.LINE
				go.Position = UDim2.new(1, -66, 0.5, -14)
				go.Size = UDim2.fromOffset(58, 28)
				go.Activated:Connect(function()
					Net.get("VisitAct"):FireServer("go", entry.userId)
				end)
			end
		end
	end
	if others == 0 then
		local empty = UIKit.label(list, "지금 이 서버에 다른 사람의 섬이 없습니다", 13)
		empty.TextColor3 = UIKit.DIM
		empty.Size = UDim2.new(1, -8, 0, 40)
	end
	whereLabel.Text = "지금 있는 곳으로 기록된 섬: " .. hostName
end

function VisitUI.init(_hotbarUi)
	local _, body = UIKit.window("visit", "다른 섬 구경하기", 420, 400, Enum.KeyCode.V, function()
		Net.get("VisitAct"):FireServer("list")
	end)

	local home = UIKit.button(body, "내 섬으로 돌아가기", 14)
	home.BackgroundColor3 = UIKit.LINE
	home.Size = UDim2.new(1, 0, 0, 32)
	home.Activated:Connect(function()
		Net.get("VisitAct"):FireServer("home")
	end)

	whereLabel = UIKit.label(body, "", 12)
	whereLabel.TextColor3 = UIKit.DIM
	whereLabel.TextXAlignment = Enum.TextXAlignment.Left
	whereLabel.Position = UDim2.fromOffset(0, 38)
	whereLabel.Size = UDim2.new(1, 0, 0, 18)

	list = UIKit.scroller(body, nil, 5)
	list.Position = UDim2.fromOffset(0, 62)
	list.Size = UDim2.new(1, 0, 1, -62)

	Net.get("Visit").OnClientEvent:Connect(draw)
end

return VisitUI
