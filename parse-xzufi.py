import xml.etree.ElementTree as ET
import json
import os

class XZuFiParser:
    ns = {
        'xzufi22': 'http://xoev.de/schemata/xzufi/2_2_0'
    }

    def __init__(self, filename, out_stream):
        self.out_stream = out_stream

        self.root = ET.parse(filename).getroot()
        if self.root.attrib['xzufiVersion'] not in ['2.2', '2.2.0']:
            print("invalid xzufi version", self.root)
            raise ValueError("xzufi version not supported")

        nachrichtenkopf = self.root.findall('xzufi22:nachrichtenkopf', self.ns)
        if len(nachrichtenkopf) != 1:
            raise ValueError("The must be exactly one 'nachrichtenkopf' element")


    def tag_with_ns(self, tag, namespace):
        return '{'+self.ns[namespace]+'}'+tag

    def parse_leistung(self, tag):
        leistung = {
            'id': self.parse_identifikator(tag.find('xzufi22:id', self.ns)),
            'leika_id': tag.find('xzufi22:referenzLeiKa/code', self.ns).text
        }
        modulText_list = list(filter(lambda t: t.find('xzufi22:leikaTextmodul/code', self.ns).text == '02', tag.findall('xzufi22:modulText', self.ns)))
        assert len(modulText_list) == 1
        leistung['Leistungsbezeichnung'] = modulText_list[0].find('xzufi22:inhalt', self.ns).text
        return leistung

    def parse_spezialisierung(self, tag):
        spezialisierung = {}
        # TODO
        return spezialisierung

    def parse_identifikator(self, tag):
        identifikator = {
            'id': tag.text
        }
        if 'schemeAgencyID' in tag.attrib:
            identifikator['schemeAgencyID'] = tag.attrib['schemeAgencyID']
        if 'schemeDataURI' in tag.attrib:
            identifikator['schemeDataURI'] = tag.attrib['schemeDataURI']
        return identifikator

    def parse_zustaendigkeit(self, tag):
        leistungIDs = tag.findall('xzufi22:leistungID', self.ns)
        assert(len(leistungIDs) == 1)
        zustaendigkeit = {
            'leistungID': self.parse_identifikator(leistungIDs[0]),
            'gebietIDs': list(map(self.parse_identifikator, tag.findall('xzufi22:gebietID', self.ns)))
        }
        return zustaendigkeit

    def parse_organisationseinheit(self, tag):
        org = {}
        org_id = tag.find('xzufi22:id', self.ns)
        org['id'] = { 'value': org_id.text, 'schemeAgencyID': org_id.attrib['schemeAgencyID']}
        org['name'] = tag.find('xzufi22:name/xzufi22:name', self.ns).text
        zustaendigkeiten = list(map(self.parse_zustaendigkeit, tag.findall('xzufi22:zustaendigkeit', self.ns)))
        org['zustaendigkeiten'] = zustaendigkeiten
        return org

    def parse_onlinedienstlink(self, tag):
        link = {
            'typ': tag.find('xzufi22:typ', self.ns).attrib['listURI'] + ':' + tag.find('xzufi22:typ/code', self.ns).text,
            'link': tag.find('xzufi22:link', self.ns).text
        }
        assert link['typ'] == 'urn:xoev-de:fim:codeliste:onlinedienstlinktyp:01'
        return link

    def parse_onlinediensterweitert(self, tag):
        onlinedienst = {
            'id': self.parse_identifikator(tag.find('xzufi22:id', self.ns)),
            'Bezeichnung': tag.find('xzufi22:bezeichnung', self.ns).text
        }

        links = list(map(self.parse_onlinedienstlink, tag.findall('xzufi22:link', self.ns)))
        onlinedienst['links'] = links
        return onlinedienst

    def parse_onlinedienst_links(self):
        for child in self.root:
            if (child.tag == self.tag_with_ns('schreibe', 'xzufi22')):
                for obj in child:
                    if (obj.tag == self.tag_with_ns('onlinedienst', 'xzufi22')):
                        od = self.parse_onlinediensterweitert(obj)
                        for link in od['links']:
                            # write onlinedienst_links
                            self.out_stream.write('\n' + link['link'])
                    continue

                    if (obj.tag == self.tag_with_ns('leistung', 'xzufi22')):
                        leistung = self.parse_leistung(obj)
                        #print('Leistung:', json.dumps(self.parse_leistung(obj), indent=2))
                        #print(leistung['leika_id'])
                    elif (obj.tag == self.tag_with_ns('spezialisierung', 'xzufi22')):
                        self.parse_spezialisierung(obj)
                        #print("Spezialisierung:", json.dumps(self.parse_spezialisierung(obj), indent=2))
                    elif (obj.tag == self.tag_with_ns('organisationseinheit', 'xzufi22')):
                        self.parse_organisationseinheit(obj)
                        #print("Organisationseinheit:", json.dumps(self.parse_organisationseinheit(obj), indent=2))
                    elif (obj.tag == self.tag_with_ns('onlinedienst', 'xzufi22')):
                        self.parse_onlinediensterweitert(obj)
                        print("Onlinedienst:", json.dumps(self.parse_onlinediensterweitert(obj), indent=2))
                    else:
                        print('unknown xzufi object:', obj.tag)
                        sys.exit(1)
            elif (child.tag == self.tag_with_ns('nachrichtenkopf', 'xzufi22')):
                pass
            elif (child.tag == self.tag_with_ns('transaktionID', 'xzufi22')):
                pass
            elif (child.tag == self.tag_with_ns('transaktionPosition', 'xzufi22')):
                pass
            else:
                print('unknown tag:', child.tag)
                sys.exit(1)

def parse_file(filename, out_file):
    parser = XZuFiParser(filename, out_file)
    parser.parse_onlinedienst_links()

def parse_directory(directory, out_file):
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and filename.startswith('index') and filename.endswith('.txt'):
            #parse_file(f)
            parse_index(directory, filename, out_file)

def parse_index(directory, filename, out_file):
    print(f'##### parse_index {directory} - {filename}')
    with open(os.path.join(directory, filename), 'r') as file:
        lines = file.readlines()
        for line in lines:
            parse_file(os.path.join(directory, line.strip()), out_file)


if __name__ == "__main__":
    #parse_file('./data/service-bw/XZUFI20210828210003000000000462.xml')
    #parse_directory('./data/amt24/')
    #parse_directory('./data/service-bw/')

    with open('onlineservicelinks.txt', 'a') as out:
        for f in os.listdir('./data/pvog-fulldump'):
            path = os.path.join('./data/pvog-fulldump', f)
            print(f'##### PARSING {f}')
            if os.path.isdir(path):
                parse_directory(path, out)
