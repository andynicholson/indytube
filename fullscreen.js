/*
 * Default FlowPlayer fullscreen opener.
 */
function flowPlayerOpenFullScreen(config) {
  var winWidth = window.screen.availWidth;
  var winHeight = window.screen.availHeight;
  var fullScreenWindow = window.open('http://flv.engagemedia.org/fullscreen.html?config='+escape(config), 'EngageMedia', 'left=0,top=0,width='+winWidth+',height='+winHeight+',status=no,resizable=yes');
  }

