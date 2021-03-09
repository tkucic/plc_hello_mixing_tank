import ia_tools

proj = ia_tools.Project('plc_hello_mixing_tank.xml')

proj.Data['info']['companyName'] = 'TK Automation'
proj.Data['info']['companyURL'] = 'https://github.com/tkucic'
proj.Data['info']['contentDescription'] = 'This project is implementing a simple mixing tank with simulator. The purpose of the project is to serve as an educational platform for begginers. The project can be used under the MIT license'

proj.export('docs', 'iecMd')