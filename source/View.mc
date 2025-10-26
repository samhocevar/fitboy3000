import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

class FitBoyView extends WatchUi.WatchFace
{
    function initialize()
    {
        WatchFace.initialize();
    }

    var _batteryState, _heartRate, _totalSteps, _totalCals, _totalFloors, _bodyBattery;

    function UpdateData()
    {
        // Get battery charge state, round to integer
        _batteryState = System.getSystemStats().battery.toLong();

        // Get total number of steps and floors
        var activityInfo = ActivityMonitor.getInfo();
        _totalSteps = activityInfo != null ? activityInfo.steps : 0;
        _totalFloors = activityInfo != null ? activityInfo.floorsClimbed : 0;
        _totalCals = activityInfo != null ? activityInfo.calories : 0;

        // Get heart rate if available
        //_heartRate = Activity.Info.currentHeartRate;
        var hrData = ActivityMonitor.getHeartRateHistory(1, true).next();
        _heartRate = hrData != null && hrData.heartRate != 255 ? hrData.heartRate : -1;

        var bbData = SensorHistory.getBodyBatteryHistory({:period => 1}).next();
        _bodyBattery = bbData != null ? bbData.data.toLong() : 0;

        //var hrv = SensorHistory.getStressHistory({:period => 1}).next().data;
    }

    function onLayout(dc as Dc) as Void
    {
        setLayout(Rez.Layouts.WatchFace(dc));
    }

    // Called when this View is brought to the foreground. Restore
    // the state of this View and prepare it to be shown. This includes
    // loading resources into memory.
    var _heartSprite, _stepSprite, _ecgSprite, _batterySprite, _bluetoothSprite, _flameSprite;
    var _font;

    function onShow() as Void
    {
        _heartSprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.HeartRate});
        _stepSprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.FootSteps});
        _ecgSprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.ECG});
        _batterySprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.Battery});
        _bluetoothSprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.Bluetooth});
        _flameSprite = new WatchUi.Bitmap({:rezId => Rez.Drawables.Flame});
        _font = WatchUi.loadResource(Rez.Fonts.FitBoy3000);
    }

    function onAnimationEvent(event as AnimationEvent, options as Dictionary) as Void
    {

    }

    // Update the view
    function onUpdate(dc as Dc) as Void
    {
        UpdateData();

        // Retrieve settings
        var is12hour = !System.getDeviceSettings().is24Hour;
        var isMilitary = Application.Properties.getValue("UseMilitaryFormat");

        var fgColor = Application.Properties.getValue("ThemeColor") as Number;
        var dimColor = (fgColor >> 2) & 0x3f3f3f;

        // Get the current time and format it correctly
        var now = Time.Gregorian.info(Time.now(), Time.FORMAT_MEDIUM);
        var timeString = is12hour ? (now.hour + 11) % 12 + 1 + ":"
                       : isMilitary ? now.hour.format("%02d")
                       : now.hour + ":";
        timeString += now.min.format("%02d");

        // Update the view
        var view = View.findDrawableById("TimeLabel") as Text;
        view.setColor(fgColor);
        view.setText(timeString);

        view = View.findDrawableById("AmPmLabel") as Text;
        view.setColor(fgColor);
        view.setText(is12hour ? now.hour >= 12 ? "PM" : "AM": "");

        // Update the seconds view
        view = View.findDrawableById("SecLabel") as Text;
        view.setColor(fgColor);
        view.setText(now.sec.format("%02d"));

        // Update the date view
        view = View.findDrawableById("DateLabel") as Text;
        view.setColor(fgColor);
        view.setText(Lang.format("$1$, $3$ $2$", [now.day_of_week, now.day, now.month]));

        // Call the parent onUpdate function to redraw the layout
        View.onUpdate(dc);

        //
        // Manual stuff below
        //

        var w = dc.getWidth();
        var h = dc.getHeight();

/*
        dc.setPenWidth(1);
        dc.setColor(0x004400, Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < h; i += 3)
        {
            dc.drawLine(0, i, w, i);
        }
*/
        dc.setColor(dimColor, Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(0, h * 0.08, w * 0.46, h * 0.08);
        dc.fillRectangle(w * 0.47, h * 0.08, w, h * 0.08);
        //dc.setColor(0x000088, Graphics.COLOR_TRANSPARENT);
        //dc.fillRectangle(w * 0.75, 0, w, h);

        dc.setColor(fgColor, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w * 0.50, h * 0.08, Graphics.FONT_XTINY, Lang.format("HP $1$/100", [_bodyBattery]), Graphics.TEXT_JUSTIFY_LEFT);
        dc.drawText(w * 0.43, h * 0.08, Graphics.FONT_XTINY, Lang.format("LVL $1$", [_totalFloors]), Graphics.TEXT_JUSTIFY_RIGHT);

/*
        dc.setPenWidth(2);
        dc.drawLine(0, h * 0.16, w, h * 0.16);
        dc.drawLine(w * 0.46, h * 0.07, w * 0.46, h * 0.16);
        dc.drawLine(0, h * 0.90, w, h * 0.90);
*/

        //var hrv_x = w * 0.12, hrv_y = h * 0.48;
        var hr_x = w * 0.08, hr_y = h * 0.62;
        var steps_x = w * 0.28, steps_y = h * 0.62;
        var cal_x = w * 0.19, cal_y = h * 0.72;
        var bat_x = w * 0.32, bat_y = h * 0.91;

        //new WatchUi.Bitmap({:rezId => Rez.Drawables.ECG, :locX => hrv_x, :locY => hrv_y + h * 0.015}).draw(dc);
        //dc.drawText(hrv_x + w * 0.07, hrv_y, Graphics.FONT_SYSTEM_XTINY, Lang.format("$1$", [hrv]), Graphics.TEXT_JUSTIFY_LEFT);

        _heartSprite.setLocation(hr_x, hr_y + h * 0.015);
        _heartSprite.draw(dc);
        dc.drawText(hr_x + w * 0.07, hr_y, Graphics.FONT_SYSTEM_XTINY, _heartRate >= 0 ? _heartRate : "--", Graphics.TEXT_JUSTIFY_LEFT);

        _stepSprite.setLocation(steps_x, steps_y + h * 0.005);
        _stepSprite.draw(dc);
        dc.drawText(steps_x + w * 0.07, steps_y, Graphics.FONT_SYSTEM_XTINY, _totalSteps, Graphics.TEXT_JUSTIFY_LEFT);

        _flameSprite.setLocation(cal_x, cal_y + h * 0.01);
        _flameSprite.draw(dc);
        dc.drawText(cal_x + w * 0.07, cal_y, Graphics.FONT_SYSTEM_XTINY, _totalCals, Graphics.TEXT_JUSTIFY_LEFT);

        _batterySprite.setLocation(bat_x, bat_y - h * 0.012);
        _batterySprite.draw(dc);
        dc.drawText(bat_x + w * 0.06, bat_y, Graphics.FONT_SYSTEM_XTINY, _batteryState + "%", Graphics.TEXT_JUSTIFY_LEFT);

        _bluetoothSprite.setLocation(bat_x + w * 0.18, bat_y - h * 0.015);
        _bluetoothSprite.draw(dc);

        //new WatchUi.Bitmap({:rezId => Rez.Drawables.VaultBoy, :locX => w * 0.55, :locY => h * 0.18}).draw(dc);

        //dc.drawCircle(w * 0.5, h * 0.5, Math.sin(toto * 0.2) * 30 + 40);
        //dc.drawCircle(w / 2, h / 2, w / 2 - 1);
        dc.drawText(w * 0.53, h * 0.38, _font, toto % 8, Graphics.TEXT_JUSTIFY_LEFT);
        var dx = [ -16, -17, -18, -18, -19, -18, -18, -18 ];
        var dy = [ -23, -26, -28, -26, -23, -25, -28, -27 ];
        var head = _bodyBattery > 66 ? "a" : _bodyBattery > 33 ? "b" : "c";
        dc.drawText(w * 0.53 + 37 + dx[toto % 8], h * 0.38 - 23 + dy[toto % 8], _font, head, Graphics.TEXT_JUSTIFY_LEFT);
    }

    // Called when this View is removed from the screen. Save the
    // state of this View here. This includes freeing resources from
    // memory.
    function onHide() as Void
    {
        _heartSprite = null;
        _stepSprite = null;
        _ecgSprite = null;
        _batterySprite = null;
        _bluetoothSprite = null;
    }

    var _timer = null;
    var toto = 0;

    function _timerCallback() as Void
    {
        toto += 1;
        WatchUi.requestUpdate();
    }

    // The user has just looked at their watch. Timers and animations may be started here.
    function onExitSleep() as Void
    {
        toto = 0;
        _timer = new Toybox.Timer.Timer();
        _timer.start(method(:_timerCallback), 200, true);
    }

    // Terminate any active timers and prepare for slow updates.
    function onEnterSleep() as Void
    {
        if (_timer != null)
        {
            _timer.stop();
            _timer = null;
            toto = 0;
        }
    }
}