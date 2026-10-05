-- The screens for machines that are told what to do: choosing what an assembler makes, and which
-- item a sorter picks out. The server opens them (through "MachineInfo") when the owner uses the
-- prompt on the machine, and the choice goes back through "MachineAct".
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local Recipes = require(Shared:WaitForChild("Recipes"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local MachineUI = {}

local NAME = "machine"
local ROW = 52
local TILE = 84

type Target = { owner: number, x: number, y: number, z: number }

local target: Target? = nil
local title: TextLabel
local hint: TextLabel
local clear: TextButton
local rows: ScrollingFrame -- recipes, one to a line
local grid: ScrollingFrame -- items, as tiles
local clearAction: (() -> ())? = nil

local function send(action: string, arg: any)
	local at = target
	if at then
		Net.get("MachineAct"):FireServer(at.owner, at.x, at.y, at.z, action, arg)
	end
	Screens.close(NAME)
end

local function amounts(bag: { [string]: number }): string
	local parts = {}
	for key, n in bag do
		table.insert(parts, Defs.name(key) .. " " .. n)
	end
	table.sort(parts)
	return table.concat(parts, " · ")
end

-- One recipe on a line: picture, what it makes, what it takes.
local function recipeRow(order: number, index: number, chosen: boolean)
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
		send("recipe", index)
	end)
	row.Parent = rows
end

local function showAssembler(info)
	title.Text = "만들 것 고르기"
	hint.Text =
		"재료가 입구로 들어오면 고른 것을 만들어 내보냅니다. 전기가 있어야 돌아갑니다."
	clear.Text = "만들지 않음"
	clearAction = function()
		send("recipe", 0)
	end
	rows.Visible, grid.Visible = true, false
	UIKit.clear(rows)
	rows.CanvasPosition = Vector2.zero
	local choices = if type(info.choices) == "table" then info.choices else {}
	for order, index in choices do
		if type(index) == "number" then
			recipeRow(order, index, index == info.current)
		end
	end
end

local function showSorter(info)
	title.Text = "골라낼 것 정하기"
	hint.Text = "고른 것만 옆 출구로 나가고 나머지는 그대로 지나갑니다."
	clear.Text = "정하지 않음"
	clearAction = function()
		send("filter", "")
	end
	rows.Visible, grid.Visible = false, true
	UIKit.clear(grid)
	grid.CanvasPosition = Vector2.zero
	local order = 0
	for _, group in Defs.Palette do
		if group.tab == "아이템" then
			for _, entry in group.ids do
				local item = Defs.itemOf(entry)
				if item then
					order += 1
					local tile = UIKit.tile(grid, entry, TILE, TILE)
					tile.LayoutOrder = order
					if item == info.current then
						local stroke = tile:FindFirstChildOfClass("UIStroke")
						if stroke then
							stroke.Color = UIKit.PICK
							stroke.Thickness = 3
						end
					end
					UIKit.cover(tile, function()
						send("filter", item)
					end)
				end
			end
		end
	end
end

local function onInfo(payload: any)
	if type(payload) ~= "table" or type(payload.info) ~= "table" then
		return
	end
	local show
	if payload.kind == "assembler" then
		show = showAssembler
	elseif payload.kind == "sorter" then
		show = showSorter
	else
		return -- some other machine's screen
	end
	target = { owner = payload.owner, x = payload.x, y = payload.y, z = payload.z }
	show(payload.info)
	Screens.open(NAME)
end

function MachineUI.init(_hotbar)
	local frame, body = UIKit.window(NAME, "", 640, 470, nil, nil, function()
		target = nil
	end)
	title = frame:FindFirstChild("Title") :: TextLabel

	clear = UIKit.button(body, "", 13)
	clear.Size = UDim2.fromOffset(110, 28)
	clear.Activated:Connect(function()
		if clearAction then
			clearAction()
		end
	end)

	hint = UIKit.label(body, "", 12)
	hint.TextColor3 = UIKit.DIM
	hint.TextXAlignment = Enum.TextXAlignment.Left
	hint.Position = UDim2.fromOffset(120, 0)
	hint.Size = UDim2.new(1, -120, 0, 28)

	rows = UIKit.scroller(body, nil, 6)
	rows.Position = UDim2.fromOffset(0, 36)
	rows.Size = UDim2.new(1, 0, 1, -36)

	grid = UIKit.scroller(body, Vector2.new(TILE, TILE), 8)
	grid.Position = UDim2.fromOffset(0, 36)
	grid.Size = UDim2.new(1, 0, 1, -36)
	grid.Visible = false

	Net.get("MachineInfo").OnClientEvent:Connect(onInfo)
end

return MachineUI
