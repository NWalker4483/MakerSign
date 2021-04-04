import serial

import serial.tools.list_ports
import pygame
import pickle


class SerialMock():
    def __init__(self):
        print("WARNING: Running with mock serial. No commands will actually be sent to connected devices")

    def write(self, bytes):
        pass
class LedStrip():
    def __init__(self, led_cnt, scale = 4):
        self.initialized = False 
        self.scale = scale

        self.start_control = None
        self.end_control = None

        self.led_cnt = led_cnt

    def setup(self, vector):
        if self.start_control == None:
            self.start_control = vector
        else:
            self.move_end_control(vector)
            self.initialized = True

    def save(self):
        if self.initialized:
            return self.start_control, self.end_control, self.led_cnt
        else:
            return pygame.math.Vector2(0,0), pygame.math.Vector2(1,1), self.led_cnt

    def move_end_control(self, vector):
        self.end_control = self.start_control - \
            ((self.start_control - vector).normalize()
             * self.led_cnt * self.scale)

    def move_start_control(self, vector):
        self.start_control = self.end_control - \
            ((self.end_control - vector).normalize()
             * self.led_cnt * self.scale)

    def get_control_points(self):
        return [self.start_control, self.end_control]
class LedSymbol():
    def __init__(self, strip_lengths = None, origin = None, position = None):
        self.position = position if position != None else pygame.math.Vector2(0, 0)
        
        self.strips = []
        for length in strip_lengths:
            self.strips.append(LedStrip(length))

        self.initialized = False

    def setup(self, vector):
        strip = None
        for strip in self.strips:
            if not strip.initialized:
                strip.setup(vector)
                break
        self.initialized = all([strip.initialized for strip in self.strips])

    def save(self):
        cntrls = []
        for strip in self.strips:
            cntrls.append(strip.save())
        return cntrls
    
    def set_position(self, position):
        self.position = position
 
    def get_control_points(self):
        pnts = [[self.position]]
        for strip in self.strips:
            pnts.append(strip.get_control_points())
        print (pnts)
        return pnts

class LedSign(): # ! Should handle all pygame screen/event interactions
    def __init__(self, led_cnts, serial_port = None, position = None):
        self.position = position if position != None else pygame.math.Vector2(0, 0)

        self.symbols = []
        self.symbol_history = []  # Store the last record values in order to prevent sending duplicates unnecessrily

        for cnts in led_cnts:
            self.symbols.append(LedSymbol(cnts, origin = self.position))
            self.symbol_history.append([(0,0,0), ] * sum(cnts))  

        self.attach(serial_port)
        
        self.hold = [0, 0, 0, 0] # Dragging, Symbol_Num, Strip_Num, Is_Start
        self.adjustable = True

        self.initialized = False

       
    def set_position(self, position):
        self.position = position

    def setup(self, vector):
        symbol = None 
        for symbol in self.symbols:
            if not symbol.initialized:
                symbol.setup(vector)
                break
        self.initialized = all([symbol.initialized for symbol in self.symbols])

    def sample_screen(self, screen):
        for num, symbol in reversed(list(enumerate(self.symbols))):
            led_num = 0 
            updated = False
            for strip in symbol.strips:
                start, end = strip.get_control_points()
                unit_vector = (start - end).normalize() / strip.led_cnt
                for i in range(strip.led_cnt):
                    sample_point = self.position - symbol.position - start - (unit_vector * i)
                    try:
                        sample = screen.get_at(
                            (int(sample_point.x), int(sample_point.y)))[:-1]  # Remove A from RGBA
                    except:
                        sample = (-1, -1, -1)
                    if sample != self.symbol_history[num][i]:
                        self.symbol_history[num][i] = sample
                        self.send_cmd(num, led_num, *sample)
                        updated = True
                    led_num += 1
            if updated:
                self.send_cmd(num, 255, 0, 0, 0)    


    
    def draw(self, screen): # ! Move symbol draw code into here
        for num, symbol in enumerate(self.symbols):
            cntrl_pnts = symbol.get_control_points()
            pose = cntrl_pnts[0][0]
            pygame.draw.circle(screen, (255, 255, 0),
                                (pose.x,  pose.y), 40)
            for start, end in cntrl_pnts[1:]:
                start -= self.position - pose
                end -= self.position - pose
                mid = start - ((start - end) / 2)
                
                pygame.draw.line(screen, (255, 0, 255),
                                start, end, 6)
                
                pygame.draw.circle(screen, (255, 255, 255),
                                (int(mid.x),  int(mid.y)), 4)

                pygame.draw.circle(screen, (0, 0, 255),
                                (start.x,  start.y), 4)

                pygame.draw.circle(screen, (255, 0, 0),
                                (end.x,  end.y), 4)

                    
        #     if cntrl_pnts[0][0].distance_to(vector) < 10:
        #         self.hold[0] = 1
        #         self.hold[1] = num + 1
        #         return True
        #     strip_num = 1 
        #     for start, end in cntrl_pnts[1:]:
        # for symbol in self.symbols:
        #     # Draw Pos 
        #     for strip_num in range(len(symbol.strips) - 1):
        #             symbol.strips[strip_num].draw(screen)
        #             pygame.draw.line(
        #                 screen, (0, 0, 255), symbol.strips[strip_num].end_control, symbol.strips[strip_num + 1].start_control, 1)
                
        #         pygame.draw.circle(screen, (255, 255, 0),
        #                         (self.strips[0].start_control.x - 15,  self.strips[0].start_control.y - 15), 4)
        # if self.initialized:
        #     try:
                
        #     except:
        #         pass
        # for num, symbol in reversed(list(enumerate(self.symbols))):
        #     led_num = 0 
        #     updated = False
        #     for strip in symbol.strips:
        #         for start, end in strip.get_control_points():
        #             pass
        # if self.initialized:
      
    def adjust_controls(self, vector):
        if vector.x == -1: # Clear HOLD
            self.hold[0] = 0
        if self.hold[0] == 1:
            if self.hold[1] > 0: # Dragging Symbol
                if self.hold[2] > 0: # Dragging Strip
                    if self.hold[3] == 1: # Dragging Start
                        self.symbols[self.hold[1] - 1].strips[self.hold[2] - 1].move_start_control(self.position - self.symbols[self.hold[1] - 1].position - vector)
                    elif self.hold[3] == 2:
                        self.symbols[self.hold[1] - 1].strips[self.hold[2] - 1].move_end_control(self.position - self.symbols[self.hold[1] - 1].position - vector)
                    elif self.hold[3] == 2:
                        self.symbols[self.hold[1] - 1].strips[self.hold[2] - 1].move_end_control(self.position - self.symbols[self.hold[1] - 1].position - vector)
                else:
                    self.symbols[self.hold[1] - 1].set_position(self.position - vector)
            else:
                self.set_position(vector)
            return True

        if (self.position.distance_to(vector) < 10):
            self.hold[0] = 1
            return True
           
        for num, symbol in enumerate(self.symbols):
            cntrl_pnts = symbol.get_control_points()
            if cntrl_pnts[0][0].distance_to(vector) < 10:
                self.hold[0] = 1
                self.hold[1] = num + 1
                return True
            strip_num = 1 
            for start, end in cntrl_pnts[1:]:
                if start.distance_to(vector) < 10:
                    self.hold[0] = 1
                    self.hold[1] = num + 1
                    self.hold[2] = strip_num
                    self.hold[3] = 1
                    return True

                elif end.distance_to(vector) < 10:
                    self.hold[0] = 1
                    self.hold[1] = num + 1
                    self.hold[2] = strip_num
                    self.hold[3] = 2
                    return True
                elif False:
                    return True
                strip_num += 1
        return False

    def update(self, screen, events = []):
        if self.adjustable:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_x, mouse_y = event.pos
                        point = pygame.math.Vector2(mouse_x, mouse_y)
                        self.adjust_controls(point)
                          
                        
                elif event.type == pygame.MOUSEMOTION:
                        mouse_x, mouse_y = event.pos
                        point = pygame.math.Vector2(mouse_x, mouse_y)
                        self.adjust_controls(point)
                        
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse_x, mouse_y = event.pos
                        point = pygame.math.Vector2(-1, -1)
                        self.adjust_controls(point)

        self.sample_screen(screen)

    @staticmethod
    def load(filename):
        cntrl_vectors = []
        led_cnts = []

        # open file and read the content in a list
        with open(filename, 'r') as filehandle:
            for line in filehandle:
                if "#" in line:
                    led_cnts.append([])
                else:
                    data = line.split()
                    if len(data) == 5:
                        x1,y1,x2,y2,led_cnt = [int(i) for i in data]
                        if any([v == -1 for v in [x1,y1,x2,y2,led_cnt]]): break
                        led_cnts[-1].append(int(led_cnt))
                        cntrl_vectors.append(pygame.math.Vector2(x1, y1))
                        cntrl_vectors.append(pygame.math.Vector2(x2, y2))
                    elif len(data) == 2:
                        pass
        temp = LedSign(led_cnts)
        for vector in cntrl_vectors:
            temp.setup(vector)
        assert(temp.initialized == True)
        return temp

    def save(self, filename):
        with open(filename, 'w') as filehandle:
            for symbol in self.symbols:
                filehandle.write('#\n')
                for strip in symbol.save():
                    start, end, cnt = strip
                    filehandle.write("{} {} {} {} {}\n".format(int(start.x), int(start.y), int(end.x), int(end.y), cnt))

    def attach(self, serial_port):
        try: 
            if serial_port == None:
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    if "COM" in p:
                        serial_port = p
            self.ser = serial.Serial(serial_port, 500000)
        except Exception as e:
            print(e)
            self.ser = None # SerialMock()
        
    def send_cmd(self, device_num, led_num, R, G, B):
        """ cmd_bytearray
        0: Singifies the start of a cmd
        1: How many more times should the cmd be echod before it is executed.py
        2: Which LED should the color values be assigned to. Set to 255 in order to display all set colors
        3: Red color values 0 - 255
        4: Green color values 0 - 255
        6: Blue color values 0 - 255
        """

        values = [ord('#'), device_num, led_num, R, G, B]
        if self.ser != None:
            self.ser.write(bytearray(values))
        else:
            pass
            print("DEBUG: Device: {0} Led: {1} R: {2} G: {3} B: {4}".format(device_num, led_num, R, G, B))


# Store previous samples within the sign class object