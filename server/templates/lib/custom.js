// Our Custom D3 JavaScript here!
fetch("http://localhost:5000/api")
  .then(res => res.json()).then(renderChart)


function renderChart(data) {
  
  var timeList = [];
  var pm1List = [];
  var pm2List = [];
  var tempList = [];
  var humList = [];
  
  data = data.slice(0, 100);
  //data = data.slice(data.length - 100);
  
  data.forEach(d => {
    pm1List.push(d[0]);
    pm2List.push(d[1]);
    timeList.push(d[2]);
    humList.push(d[3]);
    tempList.push(d[4]);
  });
  
  
  var chart = c3.generate({
    bindto: '#chart',
    data: {
      x: 'x',
      xFormat: '%Y-%m-%d %H:%M:%S',
      columns: [
        ['x', ...timeList],
        ['PM 2.5', ...pm1List],
        ['PM 10', ...pm2List],
//      ['Humidity', ...humList],
//      ['Temperature',  ...tempList]
      ]
    },
    axis: {
      x: {
        type: 'timeseries',
        tick: {
          fit: true,
          format: '%Y-%m-%d %H:%M:%S'
        }
      }
    }
  });


  var avgDiv = document.getElementById('averages');
  
  document.querySelector('#averages .pm25').innerText = "Average PM 2.5 Value: "+ (pm1List.reduce((a,b) => a+b) / pm1List.length).toFixed(2);
  document.querySelector('#averages .pm10').innerText = "Average PM 10 Value: "+ (pm2List.reduce((a,b) => a+b) / pm2List.length).toFixed(2);
  document.querySelector('#averages .temperature').innerText = "Average Temperature Value: "+ (tempList.reduce((a,b) => a+b) / tempList.length).toFixed(2);
  document.querySelector('#averages .humidity').innerText = "Average Humidity Value: "+ (humList.reduce((a,b) => a+b) / humList.length).toFixed(2);
}
