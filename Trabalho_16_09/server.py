import os
import socket
import threading
import re
import datetime
 
def VerificaDiretorio():
    # Getting the current work directory (cwd) 
    thisdir = os.getcwd()   #thisdir recebe o caminho da pasta atual
 
    # r=root, d=directories, f = files
    caminhos = []
 
    #percorre pastas em busca de arquivos
    for r, d, f in os.walk(thisdir): #os.walk "caminha entre os diretorios para encontrar o arquivo especificado"
        for file in f:
            if "" in file:
                caminho_completo = (os.path.join(r, file))
                caminho_a_partir_do_host = caminho_completo.find("Trabalho_16_09")
                caminhos.append(caminho_completo[caminho_a_partir_do_host + 15:])
    
    #percorre pastas em busca de pastas
    for r, d, f in os.walk(thisdir): #os.walk "caminha entre os diretorios para encontrar o arquivo especificado"
        for file in d:
            if "" in file:
                caminho_completo = (os.path.join(r, file))
                caminho_a_partir_do_host = caminho_completo.find("Trabalho_16_09")
                caminhos.append(caminho_completo[caminho_a_partir_do_host + 15:])
    
    contador = 0
    for item in caminhos:
        caminhos[contador] = item.replace("\\", '/')
        contador += 1 
 
    caminhos_organizados = []
    for item in caminhos:
        if '.' not in item:
            caminhos_organizados.append(item)
 
    for item in caminhos:
        if item not in caminhos_organizados:
            caminhos_organizados.append(item)
 
    #print (caminhos_organizados)
    
    return caminhos_organizados
 
class HandleThreads:  #classe lidar com threads 
    def __init__(self):  
        self.threads = []   #lista de threads recebem vazio
        self.running = True  #setar a classe como ativada
    
    def newThread(self,client,fn):      #criar thread, recebendo (classe + cliente + funcao)
        th = threading.Thread(target=fn,args=(client,))  #instanciamento da thread, que espera dois parâmetros, sendo o primeiro deles o target que é o nome de uma função do seu script, no nosso caso a função worker, esse parâmetro é obrigatório. O segundo parâmetro é opcional, ele se refere aos argumentos que serão passados para a função que será executada em segundo plano, o parâmetro args espera como argumento uma tupla com os valores da função. 
        th.daemon = True  #Daemons são úteis quando o programa principal está em execução e não há problema em eliminá-los assim que os outros threads não daemon forem encerrados. Sem os encadeamentos daemon, temos que controlá-los e dizer-lhes para saírem, antes que nosso programa seja encerrado completamente. Ao defini-los como threads daemon, podemos deixá-los rodar e esquecê-los, e quando nosso programa fecha, quaisquer threads daemon são eliminados automaticamente.
        th.start()  #se der depois do daemon vai dar run time error
 
        self.threads.append(th)  #concatena o objeto da nova thread a lista de threads
        print("\nThread ",th," iniciada")
 
    def getAliveThreads(self): #funcao que verifica quais sao as threads ativas
        print("\nThreads em execução")
        for thread in self.threads:
            if thread.isAlive():
                print(thread)
        
 
    def check(self):  #funcao para remover threads que nao estao mais ativas
        while self.running:
            for thread in self.threads:
                if not thread.isAlive():
                    self.threads.remove(thread)
                    print("\nThread ",thread," encerrada. Desalocando...")
                    break
        if not self.running:
            if self.threads!=[]:
                print(len(self.threads)," threads recentes fechadas.") #len = retorna quantidade de elementos na lista
                self.threads.clear() #limpa a lista
                
 
class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #instanciando um socket tcp
        self.running = True 
        self.conns = []  #lista de connections 
        paths = VerificaDiretorio() 
        self.paths = paths.copy()
 
        self.multiThread = HandleThreads()
 
        tm = threading.Thread(target=self.multiThread.check) #instanciamento das threads
        tm.daemon = True
        tm.start()
 
        th = threading.Thread(target=self.handleInput)
        th.daemon = True
        th.start()
 
        self.autoGenerateIndex() 
 
        self.start()
 
    def autoGenerateIndex(self,path=""): #gera o index para a pagina atual
        html = '''<!DOCTYPE html>\n
        <html>\n
        <head>\n
            <title>Index</title>\n
            <meta charset="UTF-8">\n
        </head>\n
        <body>\n
            <h1>Diretorio do servidor</h1>\n
            <hr>\n
            <div class="container">\n
                <ul>\n'''
        arq = None
        items = []
        if path=="":
            arq = open("index.html","w")
            items = os.listdir(os.getcwd())
        else:
            arq = open(os.getcwd()+"\\"+path+"\\index.html","w")
            items = os.listdir(path)
        for item in items:
            if item!="index.html" and item!="server.py":
                if path.count("/")>0:
                    path = path[path.find("/")+1:]
                    html += '<li><a href="'+path+"/"+item+'">'+item+'/</a></li>\n'
                else:
                    html += '<li><a href="'+path+"/"+item+'">'+item+'/</a></li>\n'
        html += '''</ul>\n
        </div>\n
        <hr>\n
        </body>\n
        </html>\n'''
        arq.write(html)
        arq.close()
 
    def blockAll(self): #coloca timeout em todas as conexoes
        for conn in self.conns:
            conn.settimeout(1)  #tempo esgotado
 
    def handleInput(self): #lidar com entrada do usuario
        while self.running:
            cmd = input("")
            if cmd=="quit": 
                self.running = False
                self.server.setblocking(True) #mesmo que settimeout(None) // false = (0.0)
                print("Desligando...")
                self.multiThread.running = False
                self.blockAll()
            elif cmd=="getalivethreads":
                self.multiThread.getAliveThreads()
 
    def existDirectory(self,search): #verificar existencia de arquivo atraves dos caminhos
        for item in self.paths:
            if item.find(search)!=-1: #se encontrou retorne 
                return item
        return None
 
    def handleNewConnection(self,client): #lidar com nova conexao
        request = client.recv(5000).decode() #buffersize de 5000 bytes, decodifica a string usando o codec registrado para codificação. O padrão é a codificação de string padrão. 
        #print(request)
        request = request.split("\n")
        #print(request)

        if(request[0]):
            method = request[0].split() #quebra a string em palavras separadas
            print(" method [",method[0],"]")
 
            url = method[1][1:]
 
            if url.find("%20")!=-1: #se encontrar %20 no url troque por espaco
                url = url.replace("%20"," ")
 
            data = ""
            path = self.existDirectory(url) #verifica se o caminho existe
            data = "\r\nHTTP/1.1 200 OK\r\n"
            data += "Data: "+datetime.datetime.now().strftime('%d/%m/%Y %H:%M')+"\r\n"
            data += "Server: ServidorWeb\r\n"
            data += "Content-Type: text/html\r\n"
            data += "\r\n"
 
            print(data)
 
            
            if url=="" or url=="/":
                data += open("index.html","r",encoding='utf-8').read()+"\r\n\r\n"
            elif path:
                if path.find(".")==-1:
                    self.autoGenerateIndex(path)
                    data += open(path+"/index.html","r").read()+"\r\n\r\n"
                else:
                    data += open(path,"r").read()+"\r\n\r\n"    
            else:
                data = "HTTP/1.1 404 NOT FOUND\r\n"
                data += "Data: "+datetime.datetime.now().strftime('%d/%m/%Y %H:%M')+"\r\n"
                data += "Server: ServidorWeb\r\n"
                data += "Content-Type: text/html\r\n"
                data += "\r\n"
                data += "<html><body><h1>ERROR 404 NOT FOUND</h1></body></html>\r\n\r\n"
 
                print(data)
            #manda tudo e fecha a conexao
            client.sendall(data.encode())
            client.shutdown(1) # 1 desliga mas continua ouvindo caso o cliente volte
            self.conns.remove(client)
 
    def start(self):
        self.server.bind(("localhost",8080)) #liga o socket ao endereco, deve ser um endereco nao usado
        self.server.settimeout(10)  #setar o tempo limite
        self.server.listen(5) #aceitar connections
        print("Server iniciado (localhost:8080)\nDigite 'quit' para encerrar o sevidor")
 
        while self.running:
            try:
                client,address = self.server.accept() #cria a conexao 
                self.conns.append(client) #adiciona a conexao a lista
                print("Cliente: ",address,end="") 
 
                self.multiThread.newThread(client,self.handleNewConnection) #instancia a nova thread
            except:
                pass
        self.server.close()
 
server = Server()
 

