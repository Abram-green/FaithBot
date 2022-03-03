from quickchart import QuickChart
from sqldb import *


def get_stat(member):
  hours = check_online_user(member)
  hours = list(hours[-30:])
  qc = QuickChart()
  qc.height = 100

  # Config can be set as a string or as a nested dict
  qc.config = """{
    type: 'sparkline',
    data: {
      labels: """ + f"{hours}" + """,
      datasets: [
        {
          data: """ + f"{hours}" + """,
          backgroundColor: '#DCA0F8',
          borderColor: '#D180F6',
          fill: true,
          pointRadius: 1
        }
      ],
    }
  }"""
  qc.background_color = '#2F3136'
  return qc.get_short_url()
