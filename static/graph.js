Highcharts.setOptions({
  global: {
      useUTC: false
  }
});

options = {
  chart: {
      renderTo: 'graph',
      type: 'spline'
  },
  title: {
      text: 'Temperatures of the last 24h'
  },
  subtitle: {
      text: ''
  },
  colors: ['#4572A7', '#AA4643', '#89A54E', '#80699B', '#3D96AE', '#DB843D', '#92A8CD', '#A47D7C', '#B5CA92'],
  xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
          hour: '%H. %M',
      }
  },
  yAxis: {
      title: {
          text: 'Voltage'
      }
  },
  tooltip: {
      formatter: function () {
          return '<b>' + this.series.name + '</b><br/>' + Highcharts.dateFormat('%H:%M', this.x) + ': ' + this.y.toFixed(1) + 'V';
      }
  },

  plotOptions: {
      series: {
          marker: {
              radius: 2
          }
      }
  },

  lineWidth: 1,

  series: [],

  credits: {
    enabled: false
  }
}
