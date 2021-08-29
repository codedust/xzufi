import xml.etree.ElementTree as ET
import json
import os

def parseXZuFi(xml_tree):
    ns = {
        'xzufi22': 'http://xoev.de/schemata/xzufi/2_2_0'
    }

    def tag_with_ns(tag, namespace):
        return '{'+ns[namespace]+'}'+tag

    def parse_leistung(tag):
        leistung = {
            'id': parse_Identifikator(tag.find('xzufi22:id', ns)),
            'leika_id': tag.find('xzufi22:referenzLeiKa/code', ns).text
        }
        modulText_list = list(filter(lambda t: t.find('xzufi22:leikaTextmodul/code', ns).text == '02', tag.findall('xzufi22:modulText', ns)))
        assert len(modulText_list) == 1
        leistung['Leistungsbezeichnung'] = modulText_list[0].find('xzufi22:inhalt', ns).text
        return leistung

    def parse_spezialisierung(tag):
        spezialisierung = {}
        # TODO
        return spezialisierung

    def parse_Identifikator(tag):
        identifikator = {
            'id': tag.text
        }
        if 'schemeAgencyID' in tag.attrib:
            identifikator['schemeAgencyID'] = tag.attrib['schemeAgencyID']
        if 'schemeDataURI' in tag.attrib:
            identifikator['schemeDataURI'] = tag.attrib['schemeDataURI']
        return identifikator

    def parse_zustaendigkeit(tag):
        leistungIDs = tag.findall('xzufi22:leistungID', ns)
        assert(len(leistungIDs) == 1)
        zustaendigkeit = {
            'leistungID': parse_Identifikator(leistungIDs[0]),
            'gebietIDs': list(map(parse_Identifikator, tag.findall('xzufi22:gebietID', ns)))
        }
        return zustaendigkeit

    def parse_organisationseinheit(tag):
        org = {}
        org_id = tag.find('xzufi22:id', ns)
        org['id'] = { 'value': org_id.text, 'schemeAgencyID': org_id.attrib['schemeAgencyID']}
        org['name'] = tag.find('xzufi22:name/xzufi22:name', ns).text
        zustaendigkeiten = list(map(parse_zustaendigkeit, tag.findall('xzufi22:zustaendigkeit', ns)))
        org['zustaendigkeiten'] = zustaendigkeiten
        return org

    def parse_OnlinedienstLink(tag):
        link = {
            'typ': tag.find('xzufi22:typ', ns).attrib['listURI'] + ':' + tag.find('xzufi22:typ/code', ns).text,
            'link': tag.find('xzufi22:link', ns).text
        }
        assert link['typ'] == 'urn:xoev-de:fim:codeliste:onlinedienstlinktyp:01'
        return link

    def parse_OnlinedienstErweitert(tag):
        onlinedienst = {
            'id': parse_Identifikator(tag.find('xzufi22:id', ns)),
            'Bezeichnung': tag.find('xzufi22:bezeichnung', ns).text
        }

        links = list(map(parse_OnlinedienstLink, tag.findall('xzufi22:link', ns)))
        onlinedienst['links'] = links
        return onlinedienst

    root = xml_tree.getroot()
    assert root.attrib['xzufiVersion'] == '2.2.0'

    nachrichtenkopf = root.findall('xzufi22:nachrichtenkopf', ns)
    assert len(nachrichtenkopf) == 1

    for child in root:
        if (child.tag == tag_with_ns('schreibe', 'xzufi22')):
            for obj in child:
                if (obj.tag == tag_with_ns('leistung', 'xzufi22')):
                    parse_leistung(obj)
                    #print('Leistung:', json.dumps(parse_leistung(obj), indent=2))
                elif (obj.tag == tag_with_ns('spezialisierung', 'xzufi22')):
                    parse_spezialisierung(obj)
                    #print("Spezialisierung:", json.dumps(parse_spezialisierung(obj), indent=2))
                elif (obj.tag == tag_with_ns('organisationseinheit', 'xzufi22')):
                    parse_organisationseinheit(obj)
                    #print("Organisationseinheit:", json.dumps(parse_organisationseinheit(obj), indent=2))
                elif (obj.tag == tag_with_ns('onlinedienst', 'xzufi22')):
                    parse_OnlinedienstErweitert(obj)
                    #print("Onlinedienst:", json.dumps(parse_OnlinedienstErweitert(obj), indent=2))
                else:
                    print('unknown xzufi object:', obj.tag)
                    sys.exit(1)
        elif (child.tag == tag_with_ns('nachrichtenkopf', 'xzufi22')):
            print('== metadata ==')
            for metadata in nachrichtenkopf[0]:
                print(metadata.tag.replace('{'+ns['xzufi22']+'}', '')+':', metadata.text)
            print('')
        else:
            print('unknown tag:', child.tag)
            sys.exit(1)

def parse_file(filename):
    tree = ET.parse(filename)
    parseXZuFi(tree)

def parse_directory(directory):
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and f.endswith('.xml'):
            print("Parsing", f)
            parse_file(f)

if __name__ == "__main__":
    parse_directory('./data/amt24/')
    parse_directory('./data/service-bw/')
