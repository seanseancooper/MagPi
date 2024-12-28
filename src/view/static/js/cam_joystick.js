function map(x, in_min, in_max, out_min, out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

class JoystickController
{
    // stickID: ID of HTML element (representing joystick) that will be dragged
    // maxDistance: maximum amount joystick can move in any direction
    // deadzone: joystick must move at least this amount from origin to register value change
    constructor( stickID, maxDistance, deadzone )
    {
        this.id = stickID;
        let stick = document.getElementById(stickID);

        // location from which drag begins, used to calculate offsets
        this.dragStart = null;

        // track touch identifier in case multiple joysticks present
        this.touchId = null;

        this.active = false;
        this.value = { x: 0, y: 0 };
        this.last_value = { x: 0, y: 0 };

        let self = this;

        function handleDown(event)
        {
            self.active = true;

            // all drag movements are instantaneous
            stick.style.transition = '0s';

            // touch event fired before mouse event; prevent redundant mouse event from firing
            event.preventDefault();

            if (event.changedTouches)
                self.dragStart = { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY };
            else
                self.dragStart = { x: event.clientX, y: event.clientY };

            // if this is a touch event, keep track of which one
            if (event.changedTouches)
                self.touchId = event.changedTouches[0].identifier;
        }


        function handleMove(event)
        {
            if ( !self.active ) return;

            // if this is a touch event, make sure it is the right one
            // also handle multiple simultaneous touchmove events
            let touchmoveId = null;
            if (event.changedTouches)
            {
                for (let i = 0; i < event.changedTouches.length; i++)
                {
                    if (self.touchId == event.changedTouches[i].identifier)
                    {
                        touchmoveId = i;
                        event.clientX = event.changedTouches[i].clientX;
                        event.clientY = event.changedTouches[i].clientY;
                    }
                }

                if (touchmoveId == null) return;
            }

            const xDiff = event.clientX - self.dragStart.x;
            const yDiff = event.clientY - self.dragStart.y;
            const angle = Math.atan2(yDiff, xDiff);
            const distance = Math.min(maxDistance, Math.hypot(xDiff, yDiff));
            const xPosition = distance * Math.cos(angle);
            const yPosition = distance * Math.sin(angle);

            // move stick image to new position
            stick.style.transform = `translate3d(${xPosition}px, ${yPosition}px, 0px)`;

            // deadzone adjustment
            const distance2 = (distance < deadzone) ? 0 : maxDistance / (maxDistance - deadzone) * (distance - deadzone);
            const xPosition2 = distance2 * Math.cos(angle);
            const yPosition2 = distance2 * Math.sin(angle);
            const xPercent = parseFloat((xPosition2 / maxDistance).toFixed(4));
            const yPercent = -parseFloat((yPosition2 / maxDistance).toFixed(4));

            self.value = { x: xPercent, y: yPercent };

            // I think this is better, but the requests may need to be 'throttled'
            make_request()
          }

        function make_request()
        {
            let http_req = "startX: " + Math.floor(map(self.last_value.x, -1, 1, 0, 8192)) +
                       " startY: " + Math.floor(map(self.last_value.y, -1, 1, 8192, 0)) +
                       " endX: " + Math.floor(map(self.value.x, -1, 1, 0, 8192))+
                       " endY: " + Math.floor(map(self.value.y, -1, 1, 8192, 0))

            //console.log(http_req)
            const xhttp = new XMLHttpRequest();

            // NOTE: this is a local, internal request; the 'malformed uri' is unimportant.
            const PROTOCOL = 'http://'
            const HOST = 'localhost'
            const PORT = '5000'
            const CTX = '/cam'

            URL = PROTOCOL + HOST + ":" +  PORT + CTX + "/move/" +
                  "S_0=" + Math.floor(map(self.last_value.x, -1, 1, 0, 8192)) +
                  "&S_1=" + Math.floor(map(self.last_value.y, 1, -1, 8192, 0)) +
                  "&E_0=" + Math.floor(map(self.value.x, -1, 1, 0, 8192)) +
                  "&E_1=" + Math.floor(map(self.value.y, 1, -1, 8192, 0))

            xhttp.open("GET", URL);
            xhttp.send();

            //console.log(xhttp.getAllResponseHeaders())
        }

        function handleUp(event)
        {
            if ( !self.active ) return;

            // if this is a touch event, make sure it is the right one
            if (event.changedTouches && self.touchId != event.changedTouches[0].identifier) return;

            // transition the joystick position back to center
            stick.style.transition = '.5s';
            stick.style.transform = `translate3d(0px, 0px, 0px)`;

            //make_request()

            // reset everything
            self.last_value = { x: self.value.x , y: self.value.y  };
            self.value = { x: 0, y: 0 };
            self.touchId = null;
            self.active = false;
        }

        stick.addEventListener('mousedown', handleDown);
        stick.addEventListener('touchstart', handleDown);
        document.addEventListener('mousemove', handleMove, {passive: false});
        document.addEventListener('touchmove', handleMove, {passive: false});
        document.addEventListener('mouseup', handleUp);
        document.addEventListener('touchend', handleUp);
    }
}

let joystick = new JoystickController("stick1", 48, 8);

function update()
{
    document.getElementById("joy_status").innerText = "Joystick: " + JSON.stringify(joystick.value);
    document.getElementById("x_mapped").innerText = "X: " + JSON.stringify(Math.floor(map(joystick.value.x, -1, 1, 0, 8192)));
    document.getElementById("y_mapped").innerText = "Y: " + JSON.stringify(Math.floor(map(joystick.value.y, 1, -1, 8192, 0)));
    document.getElementById("last_x_mapped").innerText = "lastX: " + JSON.stringify(Math.floor(map(joystick.last_value.x, -1, 1, 0, 8192)));
    document.getElementById("last_y_mapped").innerText = "lastY: " + JSON.stringify(Math.floor(map(joystick.last_value.y, 1, -1, 8192, 0)));
}

function loop()
{
    requestAnimationFrame(loop);
    update();
}

loop();

