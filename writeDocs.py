import ia_tools

proj = ia_tools.Project('plc_hello_mixing_tank.xml')

proj.Data['info']['companyName'] = 'TK Automation'
proj.Data['info']['companyURL'] = 'https://github.com/tkucic'
proj.Data['info']['contentDescription'] = 'In idustrial automation the "hello world" program is a mixing tank. As a part of my portfolio I have written a simple mixing tank controller and a simulator. The project is meant for begginers and for educational purposes. It is published under MIT license. Written in CODESYS 3.5 and in structured text language.\nThe project is designed in a way that the user can disable the main program and replace it with his own implementation. Simulator and the HMI sees only the IO and HMI global variables so if the user wishes to create an own implementation those variables should be written. On the simulator side the operator can see if the implementation is working correctly.'

proj.export('docs', 'iecMd')