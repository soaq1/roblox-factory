-- The row of buttons at the top of the screen: bag, crafting, trade, visiting, settings, and home.
-- Everything a key opens can also be reached here, so nothing needs a keyboard.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Net"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local MenuButtons = {}

local WIDTH, HEIGHT, GAP = 62, 44, 6

function MenuButtons.init(hotbar)
	local buttons = {
		{
			text = "가방",
			run = function()
				hotbar.openInventory()
			end,
		},
		{
			text = "조합",
			run = function()
				Screens.toggle("craft")
			end,
		},
		{
			text = "거래",
			run = function()
				Screens.toggle("trade")
			end,
		},
		{
			text = "섬 구경",
			run = function()
				Screens.toggle("visit")
			end,
		},
		{
			text = "설정",
			run = function()
				Screens.toggle("settings")
			end,
		},
		{
			-- Always there: takes the player to their own island from wherever they are.
			text = "홈",
			home = true,
			run = function()
				Screens.closeAll()
				Net.get("VisitAct"):FireServer("home")
			end,
		},
	}

	local row = Instance.new("Frame")
	row.Name = "Menu"
	row.BackgroundTransparency = 1
	row.AnchorPoint = Vector2.new(0.5, 0)
	row.Position = UDim2.new(0.5, 0, 0, 4)
	row.Size = UDim2.fromOffset(#buttons * (WIDTH + GAP) - GAP, HEIGHT)
	row.Parent = Screens.gui()
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, GAP)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = row
	-- Narrower than the row (a phone held upright): shrink it to fit.
	local fit = Instance.new("UIScale")
	fit.Parent = row
	local function refit()
		local room = UIKit.viewport().X - 16
		fit.Scale = math.clamp(room / row.Size.X.Offset, 0.5, 1)
	end
	refit()
	Screens.gui():GetPropertyChangedSignal("AbsoluteSize"):Connect(refit)

	for order, entry in buttons do
		local item = UIKit.button(row, entry.text, 13)
		item.Size = UDim2.fromOffset(WIDTH, HEIGHT)
		item.LayoutOrder = order
		item.BackgroundColor3 = UIKit.BACK
		item.BackgroundTransparency = 0.15
		UIKit.stroke(item, if entry.home then UIKit.PICK else UIKit.LINE)
		item.Activated:Connect(entry.run)
	end
end

return MenuButtons
