import xml.etree.ElementTree as ET

def get_sample_rate(inFileName):
    """Finds sample rate for a ThorSync .xml file
    usage:
    sampleRateHz = parse_thor_xml.get_sample_rate(inFileName)

    PTW 2015-08-07"""
    tree = ET.parse(inFileName)
    root = tree.getroot()
    for child in root:
        if child.tag == 'DaqDevices':
            for grandchild in child:
                if grandchild.tag == 'AcquireBoard' and grandchild.attrib['active'] == '1':
                    for greatgrandchild in grandchild:
                        if greatgrandchild.tag == 'SampleRate' and greatgrandchild.attrib['enable'] == '1':
                            sampleRateHz = float(greatgrandchild.attrib['rate'])
                            break

    return sampleRateHz
