function getType(msg) {
  if (msg.data.indexOf('http') > -1) {
    return (msg.data.match(/(youtu|vimeo)/)) ? 'video' : 'image';
  } else {
    return 'text';
  }
}

function getRandomPosition(type) {
  var offsetX = (type !== 'text') ? 500 : 128,
    offsetY = (type !== 'text') ? 400 : 200;

  var randomWidth = ($('#results').width() - offsetX) * Math.random(),
    randomHeight = (window.innerHeight - $('#navbar').height() - offsetY) * Math.random();

  if (randomWidth < offLimits[0].width && randomHeight < offLimits[0].height) {
    randomHeight += offLimits[0].height;
  }
  
  // Code to come later for avoiding notification boxes

  return {
    top: randomHeight,
    left: randomWidth
  }
}

function placeTile(msg) {
  var type = getType(msg);
  var randomPos = getRandomPosition(type);

  var $li = $('<li class="'+type+'" style="top:'+randomPos.top+';left:'+randomPos.left+';"></li>')

  switch (type) {
    case 'text':
      $li.html('<p>' + msg.data + '</p>');
      break;
    case 'image':
      $li.html('<img style="max-width: 500px;" src="'+ msg.data +'" />');
      break;
    case 'video':
      var url = msg.data.split('watch?v=')[1];
      $li.html('<iframe width="560" height="315" src="https://www.youtube.com/embed/'+ url +'?rel=0&amp;autoplay=1&amp;controls=0&amp;showinfo=0" frameborder="0" allowfullscreen></iframe>');
      break;
  }

  $('#results ul').append($li);
}

$(document).ready(function(){
  var protocol = (window.location.href.indexOf('https') > -1) ? 'https://' : 'http://';
  var socket = io.connect(protocol + document.domain + ':' + location.port + '/text');

  // So that newly placed cards don't go above/underneath UI elements
  window.offLimits = [{  // First is the number in the top left that we 
    'x': 0,           // know will be there.
    'y': 0,
    'width': $('#number').width() + 30,  // Margin is 20, plus 10 padding
    'height': $('#number').height() + 40 // Margin is 30, plus 10 padding
  }]
  socket.on('response', placeTile);

  var start = new Date(),
    end = new Date();
  end.setDate(end.getDate() + 1);
  start.setDate(end.getDate() - 7);
  $.get('/texts?start=' + start.toString() + '&end=' + end.toString(), function(texts) {
    texts = JSON.parse(texts);
    for (var i=0; i<texts.length; i++) placeTile(texts[i]);
  })
});