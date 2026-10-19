{
  "description": "Manual dev-only clause annotations for diagnosis; never use these annotations at test time or as a trained parser.",
  "cases": [
    {
      "claim": "William M O Dawson is actually the successor of Albert B White.",
      "group": "label_review",
      "note": "The literal claim has one successor clause, which is a connected path. Original Evidence additionally names a birthplace/Tonga condition absent from the text; verify dataset provenance before calling this a V4 error.",
      "clauses": [
        {
          "name": "Albert B. White's successor is William M. O. Dawson",
          "support_any": [
            ["Albert_B._White", "successor", "William_M._O._Dawson"],
            ["William_M._O._Dawson", "~successor", "Albert_B._White"]
          ]
        }
      ]
    },
    {
      "claim": "Bandeja paisa is made in the Antioquia Department of Colombia.",
      "group": "label_review",
      "note": "The region and country clauses appear in connected paths, while original Evidence additionally names an ingredient/Brown sugar condition absent from the text. Verify the original example and generation process.",
      "clauses": [
        {
          "name": "Bandeja paisa has region Antioquia Department",
          "support_any": [
            ["Antioquia_Department", "~region", "Bandeja_paisa"],
            ["Bandeja_paisa", "region", "Antioquia_Department"]
          ]
        },
        {
          "name": "Antioquia Department is in Colombia",
          "support_any": [
            ["Antioquia_Department", "country", "Colombia"],
            ["Colombia", "~country", "Antioquia_Department"]
          ]
        }
      ]
    },
    {
      "claim": "Acme Airport is located in Asherton, Texas in the United States.",
      "group": "partial_false",
      "clauses": [
        {
          "name": "Acme Airport is located in Asherton, Texas",
          "support_any": [
            ["Acme_Airport", "location", "Asherton,_Texas"],
            ["Asherton,_Texas", "~location", "Acme_Airport"]
          ]
        },
        {
          "name": "Asherton, Texas is in the United States",
          "support_any": [
            ["Asherton,_Texas", "country", "United_States"],
            ["United_States", "~country", "Asherton,_Texas"]
          ]
        }
      ]
    },
    {
      "claim": "Yeah, Aurakles was created by Ian James Corlett and Len Wein!",
      "group": "partial_false",
      "clauses": [
        {
          "name": "Aurakles was created by Ian James Corlett",
          "support_any": [
            ["Aurakles", "creator", "Ian_James_Corlett"],
            ["Ian_James_Corlett", "~creator", "Aurakles"]
          ]
        },
        {
          "name": "Aurakles was created by Len Wein",
          "support_any": [
            ["Aurakles", "creator", "Len_Wein"],
            ["Len_Wein", "~creator", "Aurakles"]
          ]
        }
      ]
    },
    {
      "claim": "Bandeja paisa (white wine) is part of Colombian cuisine.",
      "group": "partial_false",
      "clauses": [
        {
          "name": "Bandeja paisa contains white wine",
          "support_any": [
            ["Bandeja_paisa", "ingredient", "White_wine"],
            ["White_wine", "~ingredient", "Bandeja_paisa"]
          ]
        },
        {
          "name": "Bandeja paisa belongs to Colombian cuisine",
          "support_any": [
            ["Bandeja_paisa", "country", "Colombian_cuisine"],
            ["Colombian_cuisine", "~country", "Bandeja_paisa"]
          ]
        }
      ]
    },
    {
      "claim": "Ciudad Ayala is in the Pacific Standard time zone and in its version, UTC+04:30.",
      "group": "partial_false",
      "clauses": [
        {
          "name": "Ciudad Ayala has Pacific Standard Time Zone",
          "support_any": [
            ["Ciudad_Ayala", "timeZone", "Pacific_Standard_Time_Zone"],
            ["Pacific_Standard_Time_Zone", "~timeZone", "Ciudad_Ayala"]
          ]
        },
        {
          "name": "Ciudad Ayala has UTC+04:30 time zone",
          "support_any": [
            ["Ciudad_Ayala", "timeZone", "UTC+04:30"],
            ["UTC+04:30", "~timeZone", "Ciudad_Ayala"]
          ]
        }
      ]
    },
    {
      "claim": "It covers the academic discipline of analytic philosophy. The LCCN number is 83646315.",
      "group": "partial_false",
      "clauses": [
        {
          "name": "Acta Mathematica Hungarica has discipline Analytic philosophy",
          "support_any": [
            ["Acta_Mathematica_Hungarica", "discipline", "Analytic_philosophy"],
            ["Analytic_philosophy", "~discipline", "Acta_Mathematica_Hungarica"]
          ]
        },
        {
          "name": "Acta Mathematica Hungarica has LCCN 83646315",
          "support_any": [
            ["Acta_Mathematica_Hungarica", "lccn", "\"83646315\""],
            ["\"83646315\"", "~lccn", "Acta_Mathematica_Hungarica"]
          ]
        }
      ]
    },
    {
      "claim": "Arrabbiata sauce is from the Rome region and has chili pepper in it.",
      "group": "true_control",
      "clauses": [
        {
          "name": "Arrabbiata sauce is from Rome",
          "support_any": [
            ["Arrabbiata_sauce", "region", "\"Rome\""],
            ["\"Rome\"", "~region", "Arrabbiata_sauce"],
            ["Arrabbiata_sauce", "region", "Rome"]
          ]
        },
        {
          "name": "Arrabbiata sauce contains chili pepper",
          "support_any": [
            ["Arrabbiata_sauce", "ingredient", "Chili_pepper"],
            ["Chili_pepper", "~ingredient", "Arrabbiata_sauce"]
          ]
        }
      ]
    },
    {
      "claim": "Tomatoes from the order Solanales are used in Arrabbiata sauce!",
      "group": "true_control",
      "clauses": [
        {
          "name": "Tomato is of order Solanales",
          "support_any": [
            ["Tomato", "order", "Solanales"],
            ["Solanales", "~order", "Tomato"]
          ]
        },
        {
          "name": "Arrabbiata sauce contains Tomato",
          "support_any": [
            ["Arrabbiata_sauce", "ingredient", "Tomato"],
            ["Tomato", "~ingredient", "Arrabbiata_sauce"]
          ]
        }
      ]
    }
  ]
}
